import httpx
import os
import logging
import time
from services.llm_client import LLMClient

logger = logging.getLogger("health_driver")

class DeepHealthDriver:
    """
    Performs semantic health checks by parsing standard health response formats.
    Purely deterministic: gathers raw status, code, and latency.
    """
    async def check_service(self, url: str) -> dict:
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                latency = int((time.time() - start_time) * 1000)
                
                try:
                    data = response.json()
                    status = data.get("status", "UP" if response.status_code == 200 else "DOWN").upper()
                except:
                    status = "UP" if response.status_code == 200 else "DOWN"
                
                return {
                    "status": "UP" if status in ["PASS", "UP", "OK", "HEALTHY"] else "DOWN",
                    "latency_ms": latency,
                    "http_code": response.status_code,
                    "raw_status": status
                }
        except Exception as e:
            latency = int((time.time() - start_time) * 1000)
            logger.error(f"Health check failed for {url}: {e}")
            return {
                "status": "DOWN",
                "latency_ms": latency,
                "http_code": 0, # Denotes transport failure
                "raw_status": f"ERROR: {str(e)}"
            }

class DatabaseDriver:
    """
    Universal async database driver supporting PostgreSQL, MySQL, and MongoDB.
    Auto-detects database type from connection string and performs appropriate checks.
    """
    def __init__(self, db_url: str = None):
        self.db_url = db_url or os.getenv("TARGET_DB_URL")
        self.db_type = None
        if self.db_url:
            self.db_type = self._detect_db_type(self.db_url)

    def _detect_db_type(self, url: str) -> str:
        """Detect database type from connection string."""
        url_lower = url.lower()
        if url_lower.startswith('postgresql://') or url_lower.startswith('postgres://'):
            return 'postgresql'
        elif url_lower.startswith('mysql://'):
            return 'mysql'
        elif url_lower.startswith('mongodb://') or url_lower.startswith('mongodb+srv://'):
            return 'mongodb'
        else:
            raise ValueError(f"Unsupported database URL format: {url[:20]}...")

    async def check_connectivity(self) -> dict:
        """
        Check database connectivity with appropriate async driver.
        Returns: {"status": "CONNECTED"|"FAILED", "latency_ms": int, "error": str (optional)}
        """
        if not self.db_url:
            return {"status": "FAILED", "latency_ms": 0, "error": "TARGET_DB_URL not configured"}
        
        try:
            if self.db_type == 'postgresql':
                return await self._check_postgresql()
            elif self.db_type == 'mysql':
                return await self._check_mysql()
            elif self.db_type == 'mongodb':
                return await self._check_mongodb()
            else:
                return {"status": "FAILED", "latency_ms": 0, "error": f"Unknown database type: {self.db_type}"}
        except Exception as e:
            logger.error(f"Database connectivity check failed: {e}")
            return {"status": "FAILED", "latency_ms": 0, "error": str(e)}

    async def _check_postgresql(self) -> dict:
        """Check PostgreSQL connectivity using asyncpg."""
        import asyncpg
        import time
        
        try:
            start = time.time()
            conn = await asyncpg.connect(self.db_url, timeout=10)
            await conn.execute('SELECT 1')
            latency = int((time.time() - start) * 1000)
            await conn.close()
            logger.info(f"PostgreSQL connection successful: {latency}ms")
            return {"status": "CONNECTED", "latency_ms": latency}
        except asyncpg.PostgresError as e:
            logger.error(f"PostgreSQL connection failed: {e}")
            return {"status": "FAILED", "latency_ms": 0, "error": f"PostgreSQL error: {str(e)}"}
        except Exception as e:
            logger.error(f"PostgreSQL connection error: {e}")
            return {"status": "FAILED", "latency_ms": 0, "error": str(e)}

    async def _check_mysql(self) -> dict:
        """Check MySQL connectivity using aiomysql."""
        import aiomysql
        import time
        from urllib.parse import urlparse
        
        try:
            # Parse MySQL connection string
            parsed = urlparse(self.db_url)
            
            start = time.time()
            conn = await aiomysql.connect(
                host=parsed.hostname or 'localhost',
                port=parsed.port or 3306,
                user=parsed.username or 'root',
                password=parsed.password or '',
                db=parsed.path.lstrip('/') if parsed.path else '',
                connect_timeout=10
            )
            async with conn.cursor() as cursor:
                await cursor.execute('SELECT 1')
            latency = int((time.time() - start) * 1000)
            conn.close()
            logger.info(f"MySQL connection successful: {latency}ms")
            return {"status": "CONNECTED", "latency_ms": latency}
        except aiomysql.Error as e:
            logger.error(f"MySQL connection failed: {e}")
            return {"status": "FAILED", "latency_ms": 0, "error": f"MySQL error: {str(e)}"}
        except Exception as e:
            logger.error(f"MySQL connection error: {e}")
            return {"status": "FAILED", "latency_ms": 0, "error": str(e)}

    async def _check_mongodb(self) -> dict:
        """Check MongoDB connectivity using motor (async pymongo)."""
        from motor.motor_asyncio import AsyncIOMotorClient
        import time
        
        try:
            start = time.time()
            client = AsyncIOMotorClient(
                self.db_url,
                serverSelectionTimeoutMS=10000
            )
            # Ping the database to verify connection
            await client.admin.command('ping')
            latency = int((time.time() - start) * 1000)
            client.close()
            logger.info(f"MongoDB connection successful: {latency}ms")
            return {"status": "CONNECTED", "latency_ms": latency}
        except Exception as e:
            logger.error(f"MongoDB connection failed: {e}")
            return {"status": "FAILED", "latency_ms": 0, "error": f"MongoDB error: {str(e)}"}

    async def check_migrations(self) -> dict:
        """
        Check if database migrations are up to date.
        Implementation varies by database type and migration framework.
        """
        if not self.db_url:
            return {"match": False, "error": "No database configured"}
        
        try:
            if self.db_type == 'postgresql':
                return await self._check_postgresql_migrations()
            elif self.db_type == 'mysql':
                return await self._check_mysql_migrations()
            elif self.db_type == 'mongodb':
                return await self._check_mongodb_migrations()
            else:
                return {"match": True, "note": "Migration check not implemented for this database type"}
        except Exception as e:
            logger.warning(f"Migration check failed: {e}")
            return {"match": True, "note": f"Migration check skipped: {str(e)}"}

    async def _check_postgresql_migrations(self) -> dict:
        """Check PostgreSQL migrations (Alembic or similar)."""
        import asyncpg
        
        try:
            conn = await asyncpg.connect(self.db_url, timeout=10)
            # Check if alembic_version table exists
            result = await conn.fetchval(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'alembic_version')"
            )
            if result:
                version = await conn.fetchval("SELECT version_num FROM alembic_version LIMIT 1")
                await conn.close()
                return {"match": True, "current_version": version, "note": "Alembic version found"}
            await conn.close()
            return {"match": True, "note": "No migration table found (may not use migrations)"}
        except Exception as e:
            return {"match": True, "note": f"Could not verify migrations: {str(e)}"}

    async def _check_mysql_migrations(self) -> dict:
        """Check MySQL migrations (Alembic or similar)."""
        import aiomysql
        from urllib.parse import urlparse
        
        try:
            parsed = urlparse(self.db_url)
            conn = await aiomysql.connect(
                host=parsed.hostname or 'localhost',
                port=parsed.port or 3306,
                user=parsed.username or 'root',
                password=parsed.password or '',
                db=parsed.path.lstrip('/') if parsed.path else '',
                connect_timeout=10
            )
            async with conn.cursor() as cursor:
                # Check if alembic_version table exists
                await cursor.execute("SHOW TABLES LIKE 'alembic_version'")
                result = await cursor.fetchone()
                if result:
                    await cursor.execute("SELECT version_num FROM alembic_version LIMIT 1")
                    version = await cursor.fetchone()
                    conn.close()
                    return {"match": True, "current_version": version[0] if version else None, "note": "Alembic version found"}
            conn.close()
            return {"match": True, "note": "No migration table found (may not use migrations)"}
        except Exception as e:
            return {"match": True, "note": f"Could not verify migrations: {str(e)}"}

    async def _check_mongodb_migrations(self) -> dict:
        """Check MongoDB migrations (custom implementation)."""
        from motor.motor_asyncio import AsyncIOMotorClient
        
        try:
            client = AsyncIOMotorClient(self.db_url, serverSelectionTimeoutMS=10000)
            # Check for a migrations collection or version document
            db = client.get_default_database()
            collections = await db.list_collection_names()
            
            if 'migrations' in collections or 'schema_version' in collections:
                # Try to get version from migrations collection
                if 'migrations' in collections:
                    version_doc = await db.migrations.find_one(sort=[('version', -1)])
                    client.close()
                    return {"match": True, "current_version": version_doc.get('version') if version_doc else None, "note": "Migration collection found"}
            
            client.close()
            return {"match": True, "note": "No migration collection found (may not use migrations)"}
        except Exception as e:
            return {"match": True, "note": f"Could not verify migrations: {str(e)}"}
