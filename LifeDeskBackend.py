from abc import abstractmethod,ABC
import datetime as dt
import mysql.connector as mslc
import speedtest
import bcrypt as bt
from werkzeug.security import check_password_hash,generate_password_hash
import json
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import pandas as pd

# Module-level global user id. Use string "0" when no user is set.
CURRENT_USER_ID = "0"

def set_current_user_id(uid):
    global CURRENT_USER_ID
    try:
        # store as string for consistent "0" behavior
        CURRENT_USER_ID = str(uid) if uid is not None else "0"
    except Exception:
        CURRENT_USER_ID = "0"

def get_current_user_id():
    return CURRENT_USER_ID

def serialize_db_result(result):
    """Convert database results to JSON-serializable format"""
    if isinstance(result, list):
        return [serialize_db_result(item) for item in result]
    
    if isinstance(result, dict):
        serialized = {}
        for key, value in result.items():
            if isinstance(value, bytes):
                try:
                    serialized[key] = value.decode('utf-8')
                except:
                    serialized[key] = str(value)
            elif isinstance(value, dt.datetime):
                serialized[key] = value.isoformat()
            elif key in ['server', 'data'] and isinstance(value, str):
                try:
                    serialized[key] = json.loads(value)
                except:
                    serialized[key] = value
            else:
                serialized[key] = value
        return serialized
    
    if isinstance(result, bytes):
        try:
            return result.decode('utf-8')
        except:
            return str(result)
    
    if isinstance(result, dt.datetime):
        return result.isoformat()
    
    return result

class LifeDesk(ABC):
    def __init__(self, user_id=None):
        try:
            # Set instance user id from passed value or global
            self.user_id = str(user_id) if user_id is not None else get_current_user_id() or "0"
            if not self.user_id:
                self.user_id = "0"

            self.conn = mslc.connect(host="localhost", user="root", database="life_desk",connection_timeout=5)
            self.cursor = self.conn.cursor(dictionary=True)
            if self.conn.is_connected():
                print("Connection Successful")
            else:
                print("Connection Unsuccessful")
                print("System Exiting.....")
                SystemExit
            db_name="life_desk"
            self.cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        except (ConnectionError,TimeoutError,ConnectionRefusedError,ModuleNotFoundError) as E:
            print("Error : ",E)
    def test(self, password, email):
        try:
            # Ensure parameter is passed as a single-element tuple
            self.cursor.execute("SELECT encrypted_password FROM users WHERE email = %s ", (email,))
            row = self.cursor.fetchone()
            if not row:
                return False
            stored_hash = row.get("encrypted_password")
            return check_password_hash(stored_hash, password)
        except (mslc.Error,Exception) as E:
            print("Error : ",E)
class LifeDeskManager(LifeDesk):
    def __init__(self, user_id=None):
        super().__init__(user_id=user_id)
        try:
            self.user_id = str(user_id) if user_id is not None else get_current_user_id() or "0"
            self.conn = mslc.connect(host="localhost", user="root", database="life_desk")
            self.cursor = self.conn.cursor(dictionary=True)
            if self.conn.is_connected():
                print("Connection Successful")
                self.Create_users_table()
            else:
                print("Connection Unsuccessful")
                SystemExit
        except (ConnectionError, TimeoutError, ConnectionRefusedError, ModuleNotFoundError) as E:
            print("Error : ", E)
    def Create_users_table(self):
        try:
            self.cursor.execute("""
                SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = 'life_desk' AND TABLE_NAME = 'users'
            """)
            if self.cursor.fetchone():
                print("Users table already exists")
                return
            # Create user table if it doesn't exist
            create_table_query = """CREATE TABLE IF NOT EXISTS users (
                user_id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                encrypted_password VARCHAR(255) NOT NULL,
                date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP NULL
            )
            """
            self.cursor.execute(create_table_query)
            self.conn.commit()
            print("User table created successfully")
        except mslc.Error as E:
            print(f"Error with user table: {E}")
            pass
    def verify_user(self, email, password):
        if self.test(password, email) is True:
            try:
                # Update last_login timestamp
                self.cursor.execute(
                    "UPDATE users SET last_login = NOW() WHERE email = %s",
                    (email,)
                )
                self.conn.commit()
                # Fetch and return user data
                self.cursor.execute("SELECT user_id, email FROM users WHERE email = %s", (email,))
                user = self.cursor.fetchone()
                # set global current user id
                if user and user.get('user_id'):
                    set_current_user_id(user.get('user_id'))
                    self.user_id = str(user.get('user_id'))
                return user
            except mslc.Error as E:
                print("Error fetching user data:", E)
                return None
        return None
    def register_user(self, email, password):
        try:
            # Check if user already exists
            self.cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
            if self.cursor.fetchone():
                return {
                    "success": False,
                    "message": "User already exists",
                    "status_code": 409
                }
            hashed_password = generate_password_hash(password)
            self.cursor.execute(
                "INSERT INTO users (email, encrypted_password) VALUES (%s, %s)",
                (email, hashed_password)
            )
            self.conn.commit()
            # capture and set the new user id globally
            new_id = getattr(self.cursor, 'lastrowid', None)
            if new_id:
                set_current_user_id(new_id)
                self.user_id = str(new_id)
            return {
                "success": True,
                "message": "Registration successful",
                "status_code": 201,
                "user_id": new_id or None
            }
        except mslc.Error as E:
            print(f"Database error during registration: {E}")
            return {
                "success": False,
                "message": f"Database error: {str(E)}",
                "status_code": 500
            }
        except Exception as E:
            print(f"Error during registration: {E}")
            return {
                "success": False,
                "message": f"Registration failed: {str(E)}",
                "status_code": 500
            }
class Speedtest(LifeDesk):
    def __init__(self, user_id=None):
        try:
            # set instance user id
            self.user_id = str(user_id) if user_id is not None else get_current_user_id() or "0"
            self.ST = speedtest.Speedtest()
            print(self.ST)
        except Exception as E:
            print(f"Warning: Speedtest initialization failed: {E}")
            self.Error2=E
            self.ST=None
    def run_and_stream(self):
        import threading
        import queue

        if not self.ST:
            yield {"status": "error", "message": {self.Error2}}
            return

        try:
            yield {"status": "starting"}
            yield {"status": "selecting_best_server"}

            # ---------- DOWNLOAD ----------

            yield {"status": "running_download"}
            download_queue = queue.Queue()

            def download_worker():
                try:
                    download_speed = self.ST.download(
                        callback=lambda *args, **kwargs: download_queue.put(args)
                    )
                    download_queue.put(("done", download_speed))
                except Exception as e:
                    download_queue.put(("error", str(e)))

            threading.Thread(target=download_worker).start()

            while True:
                item = download_queue.get()

                if item[0] == "done":
                    download_speed = item[1]
                    download_mbps = round(download_speed / 1024 / 1024, 2)
                    yield {"status": "download_done", "value": download_mbps}
                    break

                elif item[0] == "error":
                    yield {"status": "error", "message": f"Download failed: {item[1]}"}
                    return

                else:
                    d = item[0]
                    mbps = round(d / 1024 / 1024, 2)
                    yield {"status": "downloading", "value": mbps}


            # ---------- UPLOAD ----------

            yield {"status": "running_upload"}
            upload_queue = queue.Queue()

            def upload_worker():
                try:
                    upload_speed = self.ST.upload(
                        callback=lambda *args, **kwargs: upload_queue.put(args))
                    upload_queue.put(("done", upload_speed))
                except Exception as e:
                    upload_queue.put(("error", str(e)))

            threading.Thread(target=upload_worker).start()

            while True:
                item = upload_queue.get()

                if item[0] == "done":
                    upload_speed = item[1]
                    upload_mbps = round(upload_speed / 1024 / 1024, 2)
                    yield {"status": "upload_done", "value": upload_mbps}
                    break

                elif item[0] == "error":
                    yield {"status": "error", "message": f"Upload failed: {item[1]}"}
                    return

                else:
                    d = item[0]
                    mbps = round(d / 1024 / 1024, 2)
                    yield {"status": "uploading", "value": mbps}


            # ---------- LATENCY ----------

            ping = getattr(self.ST.results, "ping", None)
            ping_val = round(ping, 2) if ping else None

            if ping_val is not None:
                yield {"status": "ping", "value": ping_val}


            # ---------- FINAL ----------

            yield {
                "status": "done",
                "download": download_mbps,
                "upload": upload_mbps,
                "ping": ping_val
            }
            try:
                self.conn = mslc.connect(host="localhost", user="root", database="life_desk")
                self.cursor = self.conn.cursor(dictionary=True)
                if self.conn.is_connected():
                    print("Connection Successful")
                    server_json = json.dumps({"Host" : self.ST.results.server.get('host'), "Sponsor" : self.ST.results.server.get('sponsor'),"Country" : self.ST.results.server.get('country'),"Server_Id" : self.ST.results.server.get('d')})
                    # try to store user-specific history; if user_id is "0" still store but mark as 0
                    uid = self.user_id if hasattr(self, 'user_id') else get_current_user_id() or "0"
                    query = """
                    INSERT INTO speedtesthistory
                    (user_id, server, download_speed_in_mbps, upload_speed_in_mbps, latency_in_ms)
                    VALUES (%s, %s, %s, %s, %s)
                    """
                    values = (uid, server_json,download_mbps,upload_mbps,ping_val)
                    self.cursor.execute(query, values)
                    self.conn.commit()
                    print("Everything stored")
                else:
                    print("Connection Unsuccessful")
            except (Exception) as E:
                print("Error : ",E)
        except mslc.Error as E:
            print("Database Error:", E)
        except Exception as e:
            yield {"status": "error", "message": f"Critical error: {e}"}
    def get_available_servers(self):
        server_list = []
        try:
            if not self.ST:
                return {"error": "Speedtest not initialized"}
            if not getattr(self, 'user_id', None) or self.user_id == "0":
                return "0"
            servers = self.ST.get_servers()
            for dist_list in servers.values():
                for server in dist_list:
                    server_list.append({
                        "id": server.get("id"),
                        "location": f"{server.get('name')}",
                        "country" : f"{server.get('country')}",
                        "sponsor": server.get("sponsor"),
                        "url": server.get("url")
                    })
            return server_list
        except (ValueError, BufferError, OSError) as E:
            return {"error": f"Failed to retrieve servers: {E}"}
    def get_best_servers(self):
        server_list = []
        try:
            if not self.ST:
                return {"error": "Speedtest not initialized"}
            if not getattr(self, 'user_id', None) or self.user_id == "0":
                return "0"
            best = self.ST.get_best_server()
            best_list = []
            if isinstance(best, dict):
                best_list = [best]
            elif isinstance(best, (list, tuple)):
                best_list = list(best)
            else:
                try:
                    for s in best:
                        best_list.append(s)
                except Exception as E:
                    print("Error : ",E)
            best_list = []
            for server in best_list:
                server_list.append({
                    "id": server.get("id"),
                    "location": f"{server.get('name')}",
                    "country" : f"{server.get('country')}",
                    "sponsor": server.get("sponsor"),
                    "url": server.get("url")
                })
            return server_list
        except (ValueError, BufferError, OSError) as E:
            return {"error": f"Failed to retrieve servers: {E}"}
    def speedHistory(self):
        try:
            self.conn = mslc.connect(host="localhost", user="root", database="life_desk")
            self.cursor = self.conn.cursor(dictionary=True)
            if self.conn.is_connected():
                # require a user id to fetch user-specific history
                uid = getattr(self, 'user_id', None) or get_current_user_id() or "0"
                if uid == "0":
                    return "0"
                print(uid)
                query = "SELECT * FROM speedtesthistory WHERE user_id = %s"
                self.cursor.execute(query, (uid,))
                history = self.cursor.fetchall()
                
                # Convert results to JSON-serializable format
                serializable_history = []
                for record in history:
                    serializable_record = {}
                    for key, value in record.items():
                        # Handle bytes
                        if isinstance(value, bytes):
                            try:
                                serializable_record[key] = value.decode('utf-8')
                            except:
                                serializable_record[key] = str(value)
                        # Handle datetime
                        elif isinstance(value, dt.datetime):
                            serializable_record[key] = value.isoformat()
                        # Handle JSON strings
                        elif key == 'server' and isinstance(value, str):
                            try:
                                serializable_record[key] = json.loads(value)
                            except:
                                serializable_record[key] = value
                        else:
                            serializable_record[key] = value
                    serializable_history.append(serializable_record)
                
                return serializable_history
            self.cursor.execute(query)
            self.conn.commit()
            print("Everything Displayed")
        except mslc.Error as E:
            print("Database Error:", E)
            return None
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


class PasswordManager(LifeDesk):
    def __init__(self, host="localhost", user="root", password="", database="life_desk", user_id=None):
        # set instance user id from passed value or global
        try:
            self.user_id = str(user_id) if user_id is not None else get_current_user_id() or "0"
            self.conn = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database
            )
            self.cursor = self.conn.cursor(dictionary=True)
            self._create_passwords_table()
        except (ConnectionError,ConnectionResetError) as E:
            print("Error ",E)
    
    def _create_passwords_table(self):
        """Create passwords table if it doesn't exist"""
        try:
            self.cursor.execute("""
                SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = 'life_desk' AND TABLE_NAME = 'passwords'
            """)
            if self.cursor.fetchone():
                return
            
            create_table_query = """CREATE TABLE IF NOT EXISTS passwords (
                password_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                site_name VARCHAR(255) NOT NULL,
                site_url VARCHAR(500),
                login_username VARCHAR(255) NOT NULL,
                email VARCHAR(255),
                encrypted_password VARCHAR(500) NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
            """
            self.cursor.execute(create_table_query)
            self.conn.commit()
            print("Passwords table created successfully")
        except Exception as E:
            print(f"Error creating passwords table: {E}")

    def add_password(self, user_id: int = None, site_name: str = "", site_url: str = "",
                     email: str = "", login_username: str = "", plain_password: str = "", notes: str = ""):
        # determine which user id to use
        try:
            uid = str(user_id) if user_id is not None else getattr(self, 'user_id', None) or get_current_user_id() or "0"
            if uid == "0":
                return "0"
            encrypted = generate_password_hash(plain_password)
            now = datetime.now()
            query = """
                INSERT INTO passwords (user_id, site_name, site_url, login_username, email,
                                    encrypted_password, notes, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            self.cursor.execute(query, (uid, site_name, site_url, login_username, email,
                                        encrypted, notes, now, now))
            self.conn.commit()
            print(f" Password for '{site_name}' added.")
        except (ConnectionAbortedError,ConnectionError,ConnectionRefusedError,TimeoutError,InterruptedError) as E:
            print("Error : ",E)
            return "Error : ",E
    def update_password(self, password_id: int, new_password: str):
        try:
            encrypted = generate_password_hash(new_password)
            now = datetime.now()
            query = """
                UPDATE passwords
                SET encrypted_password = %s, updated_at = %s
                WHERE password_id = %s
            """
            self.cursor.execute(query, (encrypted, now, password_id))
            self.conn.commit()
            if self.cursor.rowcount:
                print(f"Password ID {password_id} updated.")
            else:
                print(f"Password ID {password_id} not found.")
        except (ConnectionAbortedError,ConnectionError,ConnectionRefusedError,TimeoutError,InterruptedError) as E:
            print("Error :",E)
            return "Error :",E

    def showAllInfo(self):
        try:
            uid = getattr(self, 'user_id', None) or get_current_user_id() or "0"
            if uid == "0":
                return "0"
            query = """
                SELECT password_id, user_id, site_name, site_url, login_username,
                    encrypted_password, notes, created_at, updated_at
                FROM passwords
                WHERE user_id = %s
                ORDER BY created_at DESC
            """
            self.cursor.execute(query, (uid,))
            results = self.cursor.fetchall()
            if not results:
                print("No passwords stored.")
                return
            for r in results:
                print(f"─────────────────────────────────")
                print(f"  ID:         {r['password_id']}")
                print(f"  User ID:    {r['user_id']}")
                print(f"  Site Name:  {r['site_name']}")
                print(f"  Site URL:   {r['site_url']}")
                print(f"  Username:   {r['login_username']}")
                print(f"  Encrypted:  {r['encrypted_password'][:50]}...")
                print(f"  Notes:      {r['notes']}")
                print(f"  Created:    {r['created_at']}")
                print(f"  Updated:    {r['updated_at']}")
            print(f"─────────────────────────────────")
            print(f"Total: {len(results)} entries")
        except (ConnectionAbortedError,ConnectionError,ConnectionRefusedError,TimeoutError,InterruptedError) as E:
            print("Error :",E)
            return "Error :",E
class Performance(LifeDesk):
    def __init__(self, user_id=None):
        try:
            self.user_id = str(user_id) if user_id is not None else get_current_user_id() or "0"
            # Note: Performance data is gathered directly, no database table needed
        except Exception as E:
            print(f"Error initializing Performance: {E}")
    
    def get_system_metrics(self):
        """Gather system performance metrics"""
        try:
            import psutil
            import platform
            
            metrics = {
                "platform": platform.system(),
                "processor": platform.processor(),
                "python_version": platform.python_version(),
                "cpu_percent": psutil.cpu_percent(interval=1),
                "cpu_count": psutil.cpu_count(),
                "memory": {
                    "total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                    "available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
                    "used_gb": round(psutil.virtual_memory().used / (1024**3), 2),
                    "percent": psutil.virtual_memory().percent
                },
                "disk": {
                    "total_gb": round(psutil.disk_usage('/').total / (1024**3), 2),
                    "free_gb": round(psutil.disk_usage('/').free / (1024**3), 2),
                    "used_gb": round(psutil.disk_usage('/').used / (1024**3), 2),
                    "percent": psutil.disk_usage('/').percent
                },
                "boot_time": dt.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S"),
                "network": self._get_network_stats()
            }
            return metrics
        except ImportError:
            return {"error": "psutil not installed. Install with: pip install psutil"}
        except Exception as E:
            return {"error": str(E)}
    
    def _get_network_stats(self):
        """Get network statistics"""
        try:
            import psutil
            net = psutil.net_if_stats()
            stats = {}
            for interface, data in net.items():
                stats[interface] = {
                    "isup": data.isup,
                    "mtu": data.mtu,
                    "speed": data.speed
                }
            return stats
        except Exception as E:
            return {"error": str(E)}

    
    def AllData(self):
        """Get all system performance data"""
        return self.get_system_metrics()
    
class Analysis(LifeDesk):  
    def __init__(self, user_id=None):
        try:
            # Store both int and string versions for flexibility
            self.user_id_int = int(user_id) if user_id and str(user_id) != "0" else 0
            self.user_id = str(user_id) if user_id is not None else get_current_user_id() or "0"
            print(f"[Analysis] __init__: user_id={user_id}, user_id_int={self.user_id_int}, user_id_str={self.user_id}")
            
            self.conn = mslc.connect(host="localhost", user="root", database="life_desk")
            self.cursor = self.conn.cursor(dictionary=True)
            # ensure cursor is ready
            print(f"[Analysis] Database connected. Initialized for user_id: {self.user_id} (int: {self.user_id_int})")
        except Exception as E:
            print(f"[Analysis] Error initializing Analysis: {E}")
            import traceback
            traceback.print_exc()
            self.conn = None
            self.user_id = "0"
            self.user_id_int = 0
    
    def get_password_analysis(self):
        """Fetch password rows for the current user and return summary and rows."""
        if self.user_id == "0":
            print("[Analysis.get_password_analysis] User not authenticated")
            return {"error": "User not authenticated", "total_passwords": 0, "by_site": {}, "rows": []}

        try:
            # fetch rows - use both int and string for comparison flexibility
            q = """
                SELECT password_id, user_id, site_name, site_url, login_username, email,
                       encrypted_password, notes, created_at, updated_at
                FROM passwords
                WHERE user_id = %s
                ORDER BY created_at DESC
            """
            print(f"[Analysis.get_password_analysis] Executing query with user_id_int={self.user_id_int}")
            print(f"[Analysis.get_password_analysis] Query: {q}")
            
            self.cursor.execute(q, (self.user_id_int,))
            rows = self.cursor.fetchall() or []
            print(f"[Analysis.get_password_analysis] Query returned {len(rows)} rows")

            # SERIALIZE FIRST - convert all bytes/datetime before using data
            serial_rows = []
            for r in rows:
                rr = {}
                for k, v in r.items():
                    if isinstance(v, bytes):
                        try:
                            rr[k] = v.decode('utf-8')
                        except:
                            rr[k] = str(v)
                    elif isinstance(v, bytearray):
                        try:
                            rr[k] = bytes(v).decode('utf-8')
                        except:
                            rr[k] = str(v)
                    elif isinstance(v, dt.datetime):
                        rr[k] = v.isoformat()
                    else:
                        rr[k] = v
                serial_rows.append(rr)

            # NOW compute by_site summary from SERIALIZED rows
            by_site = {}
            for r in serial_rows:
                site = r.get('site_name') or 'unknown'
                by_site.setdefault(site, { 'count': 0, 'last_added': None })
                by_site[site]['count'] += 1
                last = r.get('created_at')
                if last:
                    # created_at is already a string from serialization
                    if not by_site[site]['last_added']:
                        by_site[site]['last_added'] = last

            total = len(serial_rows)
            print(f"[Analysis.get_password_analysis] Processing {total} passwords across {len(by_site)} sites")

            result = {
                'total_passwords': total,
                'total_sites': len(by_site),
                'by_site': by_site,
                'rows': serial_rows,
                'timestamp': dt.datetime.now().isoformat()
            }
            print(f"[Analysis.get_password_analysis] Successfully returning {total} serialized passwords")
            return result
        except Exception as E:
            print(f"[Analysis.get_password_analysis] Exception occurred: {E}")
            import traceback
            traceback.print_exc()
            return {'error': str(E), 'total_passwords': 0, 'by_site': {}, 'rows': []}
    
    def get_speedtest_analysis(self):
        """Get detailed speedtest analysis for user"""
        if self.user_id == "0":
            print("Warning: User not authenticated in get_speedtest_analysis")
            return {"error": "User not authenticated", "total_tests": 0, 'test_history': []}

        try:
            q = """
                SELECT id AS test_id, user_id, server, download_speed_in_mbps, upload_speed_in_mbps,
                       latency_in_ms, tested_at
                FROM speedtesthistory
                WHERE user_id = %s
                ORDER BY tested_at DESC
            """
            print(f"Executing speedtest query for user_id_int: {self.user_id_int}")
            self.cursor.execute(q, (self.user_id_int,))
            rows = self.cursor.fetchall() or []
            print(f"Found {len(rows)} speedtest records for user {self.user_id_int}")

            # serialize rows
            serial = []
            for r in rows:
                rr = {}
                for k, v in r.items():
                    if isinstance(v, bytes):
                        try:
                            rr[k] = v.decode('utf-8')
                        except:
                            rr[k] = str(v)
                    elif isinstance(v, dt.datetime):
                        rr[k] = v.isoformat()
                    elif k == 'server' and isinstance(v, str):
                        try:
                            rr[k] = json.loads(v)
                        except:
                            rr[k] = v
                    else:
                        rr[k] = v
                serial.append(rr)

            downloads = [r.get('download_speed_in_mbps') for r in serial if r.get('download_speed_in_mbps') is not None]
            uploads = [r.get('upload_speed_in_mbps') for r in serial if r.get('upload_speed_in_mbps') is not None]
            pings = [r.get('latency_in_ms') for r in serial if r.get('latency_in_ms') is not None]

            return {
                'total_tests': len(serial),
                'average_download_mbps': round(sum(downloads)/len(downloads),2) if downloads else 0,
                'average_upload_mbps': round(sum(uploads)/len(uploads),2) if uploads else 0,
                'average_ping_ms': round(sum(pings)/len(pings),2) if pings else 0,
                'best_download_mbps': max(downloads) if downloads else 0,
                'worst_download_mbps': min(downloads) if downloads else 0,
                'test_history': serial,
                'timestamp': dt.datetime.now().isoformat()
            }
        except Exception as E:
            print(f"Error in get_speedtest_analysis: {E}")
            import traceback
            traceback.print_exc()
            return {'error': str(E)}
    
    def generate_visualizations(self, output_dir="./analysis_reports"):
        """Generate visualizations (PNG) and CSV exports for the current user.

        Uses only the users, passwords and speedtesthistory tables.
        Returns dict with report paths and csv paths.
        """
        try:
            import os
            if self.user_id == "0":
                return {"error": "User not authenticated"}

            os.makedirs(output_dir, exist_ok=True)

            # Fetch data
            pwd = self.get_password_analysis()
            st = self.get_speedtest_analysis()

            # Fetch user info
            try:
                self.cursor.execute("SELECT user_id, email, date_created, last_login FROM users WHERE user_id = %s", (self.user_id_int,))
                user_row = self.cursor.fetchone() or {}
                user_info = {k: (v.isoformat() if isinstance(v, dt.datetime) else v) for k, v in user_row.items()} if user_row else {}
            except Exception as E:
                print(f"Error fetching user info: {E}")
                user_info = {}

            # Prepare CSVs
            csv_files = []
            # passwords CSV
            try:
                pwd_rows = pwd.get('rows', []) if isinstance(pwd, dict) else []
                if pwd_rows:
                    df_pwd = pd.DataFrame(pwd_rows)
                    pwd_csv = os.path.join(output_dir, f"user_{self.user_id_int}_passwords.csv")
                    df_pwd.to_csv(pwd_csv, index=False)
                    csv_files.append(pwd_csv)
                else:
                    pwd_csv = None
            except Exception as E:
                print("Warning: failed to write passwords CSV:", E)
                pwd_csv = None

            # speedtests CSV
            try:
                st_rows = st.get('test_history', []) if isinstance(st, dict) else []
                if st_rows:
                    df_st = pd.json_normalize(st_rows)
                    st_csv = os.path.join(output_dir, f"user_{self.user_id_int}_speedtests.csv")
                    df_st.to_csv(st_csv, index=False)
                    csv_files.append(st_csv)
                else:
                    st_csv = None
            except Exception as E:
                print("Warning: failed to write speedtests CSV:", E)
                st_csv = None

            # Build visualization
            fig, axes = plt.subplots(2, 2, figsize=(14, 10))

            # Passwords by site (top-left)
            ax1 = axes[0,0]
            if isinstance(pwd, dict) and pwd.get('by_site'):
                sites = list(pwd['by_site'].keys())
                counts = [pwd['by_site'][s]['count'] for s in sites]
                ax1.barh(sites[:20], counts[:20], color='#3b82f6')
                ax1.set_title('Passwords by Site')
                ax1.set_xlabel('Count')
            else:
                ax1.text(0.5, 0.5, 'No password data', ha='center', va='center')
                ax1.set_axis_off()

            # Speed download trend (top-right)
            ax2 = axes[0,1]
            if isinstance(st, dict) and st.get('test_history'):
                tests = st['test_history'][::-1]
                downloads = [t.get('download_speed_in_mbps') or 0 for t in tests]
                ax2.plot(downloads, marker='o', color='#10b981')
                ax2.set_title('Download Speed Trend')
                ax2.set_ylabel('Mbps')
            else:
                ax2.text(0.5, 0.5, 'No speedtest data', ha='center', va='center')
                ax2.set_axis_off()

            # Speed upload trend (bottom-left)
            ax3 = axes[1,0]
            if isinstance(st, dict) and st.get('test_history'):
                tests = st['test_history'][::-1]
                uploads = [t.get('upload_speed_in_mbps') or 0 for t in tests]
                ax3.plot(uploads, marker='s', color='#f59e0b')
                ax3.set_title('Upload Speed Trend')
                ax3.set_ylabel('Mbps')
            else:
                ax3.text(0.5, 0.5, 'No speedtest data', ha='center', va='center')
                ax3.set_axis_off()

            # Summary (bottom-right)
            ax4 = axes[1,1]
            ax4.axis('off')
            summary_lines = [f"User: {user_info.get('email', self.user_id)}"]
            summary_lines.append(f"Total Passwords: {pwd.get('total_passwords', 0) if isinstance(pwd, dict) else 0}")
            summary_lines.append(f"Unique Sites: {pwd.get('total_sites', 0) if isinstance(pwd, dict) else 0}")
            summary_lines.append(f"Total Speed Tests: {st.get('total_tests', 0) if isinstance(st, dict) else 0}")
            summary_lines.append(f"Avg Download: {st.get('average_download_mbps', 0) if isinstance(st, dict) else 0} Mbps")
            summary_lines.append(f"Avg Upload: {st.get('average_upload_mbps', 0) if isinstance(st, dict) else 0} Mbps")
            ax4.text(0.01, 0.95, '\n'.join(summary_lines), fontsize=10, va='top', family='monospace')

            plt.suptitle(f'User {self.user_id} - Analytics Report')
            plt.tight_layout(rect=[0, 0.03, 1, 0.95])

            # Save image
            png_path = os.path.join(output_dir, f"user_{self.user_id_int}_analysis.png")
            plt.savefig(png_path, dpi=150)
            plt.close(fig)

            result = {
                'success': True,
                'report_file': png_path,
                'csv_files': csv_files,
                'timestamp': dt.datetime.now().isoformat()
            }
            return result
        except Exception as E:
            print(f"Error generating visualizations: {E}")
            import traceback
            traceback.print_exc()
            return {'error': str(E)}