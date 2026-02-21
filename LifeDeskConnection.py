from flask import Flask, request, jsonify, render_template, send_file, session
from flask_cors import CORS
from LifeDeskBackend import LifeDeskManager, Speedtest, PasswordManager, Performance, Analysis, set_current_user_id, get_current_user_id, serialize_db_result
from flask import Response, stream_with_context
import json
import os

Lifedesk = Flask(__name__, template_folder='templates', static_folder='templates', static_url_path='/static')
Lifedesk.secret_key = 'lifedesk-analytics-secret-key-2024'  # For session management

CORS(Lifedesk)
backend_manager = LifeDeskManager()
password_manager = PasswordManager()

@Lifedesk.before_request
def before_request():
    """Restore user_id from session before each request"""
    if 'user_id' in session:
        set_current_user_id(session['user_id'])

@Lifedesk.route("/")
def serve_login():
    return render_template("/Home/LoginRegister/index.html")

@Lifedesk.route("/About")
def about_section():
    return render_template("/Home/about/about.html")

@Lifedesk.route("/dashboard")
def serve_dashboard():
    return render_template("/Dashboard/All_data/new.html")

@Lifedesk.route("/analytics")
def serve_analytics():
    return render_template("/Dashboard/All_data/Dashboard.html")

@Lifedesk.route("/analysis")
def serve_analysis():
    return render_template("/Dashboard/All_data/Analysis.html")

@Lifedesk.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    
    if not email or not password:
        return jsonify({"message": "Missing email or password"}), 400   
    # Use backend to register user
    result = backend_manager.register_user(email, password)
    
    if result["success"]:
        user_id = result.get("user_id")
        session['user_id'] = user_id  # Store in session
        set_current_user_id(user_id)
        return jsonify({"message": result["message"], "user_id": user_id}), 201
    else:
        return jsonify({"message": result["message"]}), result["status_code"]

# LOGIN 
@Lifedesk.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return jsonify({"message": "Missing email or password"}), 400
    # Use backend manager to verify user
    user = backend_manager.verify_user(email, password)
    if user:
        user_id = user.get("user_id")
        session['user_id'] = user_id  # Store in session
        set_current_user_id(user_id)
        return jsonify({
            "message": "Login successful",
            "email": user["email"],
            "user_id": user_id
        }), 200
    else:
        return jsonify({"message": "Invalid email or password"}), 401

@Lifedesk.route("/logout", methods=["POST"])
def logout():
    """Logout user and clear session"""
    session.clear()
    set_current_user_id("0")
    return jsonify({"message": "Logged out successfully"}), 200
    
def speedtest(lifedesk_app):
    @lifedesk_app.route("/speedtest")
    def serve_speedtest():
        return render_template("Speedtest/speedtest/speedtest.html")

    @lifedesk_app.route('/api/speedtest/stream')
    def stream_speedtest():
        def event_stream():
            st = Speedtest()
            for item in st.run_and_stream():
                try:
                    yield f"data: {json.dumps(item)}\n\n"
                except Exception:
                    yield f"data: {json.dumps({'status':'error','message':'serialization error'})}\n\n"

        return Response(stream_with_context(event_stream()), mimetype='text/event-stream')
    
    @lifedesk_app.route('/speedtest/servers')
    def serve_servers():
        return render_template("Speedtest/AllServers/servers.html")

    @lifedesk_app.route('/api/speedtest/servers')
    def api_speedtest_servers():
        st = Speedtest()
        servers = st.get_available_servers()
        if isinstance(servers, dict) and servers.get('error'):
            return jsonify(servers), 500
        return jsonify(servers)

    @lifedesk_app.route('/speedtest/best_servers')
    def serve_best_servers():
        return render_template("Speedtest/bestServer/best_server.html")

    @lifedesk_app.route('/api/speedtest/best_servers')
    def api_speedtest_best_servers():
        st = Speedtest()
        servers = st.get_available_servers()
        if isinstance(servers, dict) and servers.get('error'):
            return jsonify(servers), 500
        return jsonify(servers)
    @lifedesk_app.route("/Speedtest/History")
    def Speedtest_history():
            return render_template("Speedtest/History/speedhistory1.html")

    @lifedesk_app.route('/api/Speedtest/History')
    def api_speedtest_history():
            st = Speedtest()
            data = st.speedHistory()
            return jsonify(data)

def password_manager_routes(lifedesk_app):
    """Password Manager Routes"""
    
    @lifedesk_app.route("/passwordManager")
    def serve_password_manager():
        return render_template("passwordManager/passwordManager.html")
    
    @lifedesk_app.route("/api/passwords/add", methods=["POST"])
    def add_password():
        data = request.get_json()
        user_id = data.get("user_id")
        current_user = user_id or get_current_user_id()
        
        if current_user == "0" or not current_user:
            return jsonify({"error": "User not authenticated"}), 401
        
        site_name = data.get("site_name", "")
        site_url = data.get("site_url", "")
        email = data.get("email", "")
        login_username = data.get("login_username", "")
        plain_password = data.get("plain_password", "")
        notes = data.get("notes", "")
        
        if not all([site_name, email, login_username, plain_password]):
            return jsonify({"error": "Missing required fields"}), 400
        
        try:
            password_manager.add_password(
                user_id=int(current_user),
                site_name=site_name,
                site_url=site_url,
                email=email,
                login_username=login_username,
                plain_password=plain_password,
                notes=notes
            )
            return jsonify({"success": True, "message": "Password added successfully"}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @lifedesk_app.route("/api/passwords/all", methods=["GET"])
    def get_all_passwords():
        current_user = get_current_user_id()
        if current_user == "0":
            return jsonify({"error": "User not authenticated"}), 401
        
        try:
            pm = PasswordManager(user_id=int(current_user))
            query = """
                SELECT password_id, user_id, site_name, site_url, login_username,
                       email, notes, created_at, updated_at
                FROM passwords
                WHERE user_id = %s
                ORDER BY created_at DESC
            """
            pm.cursor.execute(query, (current_user,))
            results = pm.cursor.fetchall()
            results = serialize_db_result(results)
            return jsonify(results), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @lifedesk_app.route("/api/passwords/update/<int:password_id>", methods=["POST"])
    def update_password(password_id):
        data = request.get_json()
        user_id = data.get("user_id")
        current_user = user_id or get_current_user_id()
        
        if current_user == "0" or not current_user:
            return jsonify({"error": "User not authenticated"}), 401
        
        new_password = data.get("new_password", "")
        
        if not new_password:
            return jsonify({"error": "New password required"}), 400
        
        try:
            password_manager.update_password(password_id, new_password)
            return jsonify({"success": True, "message": "Password updated successfully"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @lifedesk_app.route("/api/passwords/delete/<int:password_id>", methods=["DELETE"])
    def delete_password(password_id):
        current_user = get_current_user_id()
        if current_user == "0":
            return jsonify({"error": "User not authenticated"}), 401
        
        try:
            pm = PasswordManager(user_id=int(current_user))
            query = "DELETE FROM passwords WHERE password_id = %s AND user_id = %s"
            pm.cursor.execute(query, (password_id, current_user))
            pm.conn.commit()
            return jsonify({"success": True, "message": "Password deleted successfully"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
# Register the routes with the Lifedesk app
speedtest(Lifedesk)
password_manager_routes(Lifedesk)
# Performance Monitoring Routes
@Lifedesk.route("/performance")
def serve_performance():
    return render_template("System_Health/performance/performance_info.html")

@Lifedesk.route("/api/performance/system-metrics", methods=["GET"])
def get_system_metrics():
    current_user = get_current_user_id()
    if current_user == "0":
        return jsonify({"error": "User not authenticated"}), 401
    
    try:
        pm = Performance(user_id=int(current_user))
        metrics = pm.get_system_metrics()
        return jsonify(metrics), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@Lifedesk.route("/api/current_user", methods=["GET"])
def api_current_user():
    user_id = get_current_user_id()
    return jsonify({"user_id": user_id}), 200


# ===== ANALYSIS ROUTES =====
# Active analysis endpoints for the dashboard

@Lifedesk.route("/api/analysis/passwords", methods=["GET"])
def api_analysis_passwords():
    """Get password analysis for current user"""
    current_user = get_current_user_id()
    print(f"[API] Password analysis request - current_user: {current_user}, type: {type(current_user)}")
    
    if current_user == "0":
        print("[API] User not authenticated (user_id = '0')")
        return jsonify({"error": "User not authenticated"}), 401
    try:
        print(f"[API] Creating Analysis object with user_id={int(current_user)}")
        analysis = Analysis(user_id=int(current_user))
        data = analysis.get_password_analysis()
        print(f"[API] Password analysis result: {data}")
        return jsonify(data), 200
    except Exception as e:
        print(f"[API] Error in password analysis: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@Lifedesk.route("/api/analysis/speedtest", methods=["GET"])
def api_analysis_speedtest():
    """Get speedtest analysis for current user"""
    current_user = get_current_user_id()
    if current_user == "0":
        return jsonify({"error": "User not authenticated"}), 401
    try:
        analysis = Analysis(user_id=int(current_user))
        data = analysis.get_speedtest_analysis()
        return jsonify(data), 200
    except Exception as e:
        print(f"Error in speedtest analysis: {e}")
        return jsonify({"error": str(e)}), 500


@Lifedesk.route('/analytic', methods=['GET'])
def api_analytic():
    """Combined analysis endpoint: returns password and speedtest summaries and generates visual assets."""
    current_user = get_current_user_id()
    if current_user == "0":
        return jsonify({"error": "User not authenticated"}), 401

    try:
        analysis = Analysis(user_id=int(current_user))

        pwd = analysis.get_password_analysis()
        st = analysis.get_speedtest_analysis()

        # Generate visualizations and CSVs (may be heavy; acceptable for on-demand)
        viz = analysis.generate_visualizations()
        if viz.get('error'):
            # still return analysis summaries but indicate viz error
            return jsonify({
                'passwords': pwd,
                'speedtests': st,
                'visualization': {'error': viz.get('error')}
            }), 200

        report_file = viz.get('report_file')
        csv_files = viz.get('csv_files', [])

        report_url = f"/api/analysis/report/{os.path.basename(report_file)}" if report_file else None
        csv_urls = [f"/api/analysis/download/{os.path.basename(p)}" for p in csv_files]

        return jsonify({
            'passwords': pwd,
            'speedtests': st,
            'visualization': {
                'report_url': report_url,
                'csv_urls': csv_urls,
                'timestamp': viz.get('timestamp')
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Active visualize route used by frontend to generate and return report URL
@Lifedesk.route("/api/analysis/visualize", methods=["GET"])
def api_analysis_visualize_active():
    """Generate and return visualization for current user (active route).

    This keeps the frontend working while legacy endpoints remain commented for reference.
    """
    current_user = get_current_user_id()
    if current_user == "0":
        return jsonify({"error": "User not authenticated"}), 401

    try:
        analysis = Analysis(user_id=int(current_user))
        result = analysis.generate_visualizations()

        if result.get('error'):
            return jsonify(result), 500

        report_file = result.get('report_file', '')
        if report_file:
            image_url = f"/api/analysis/report/{os.path.basename(report_file)}"
            return jsonify({
                "success": True,
                "report_url": image_url,
                "report_file": report_file,
                "timestamp": result.get('timestamp')
            }), 200
        return jsonify({"error": "Failed to generate report"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@Lifedesk.route('/api/analysis/download/<filename>', methods=['GET'])
def api_analysis_download(filename):
    """Serve generated CSV files for the current user."""
    current_user = get_current_user_id()
    if current_user == "0":
        return jsonify({"error": "User not authenticated"}), 401

    try:
        # basic validation
        if '..' in filename or '/' in filename:
            return jsonify({'error': 'Invalid filename'}), 400

        # ensure file belongs to current user by prefix
        if not filename.startswith(f"user_{current_user}_"):
            return jsonify({'error': 'Unauthorized'}), 403

        file_path = os.path.join('./analysis_reports', filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@Lifedesk.route('/api/analysis/export-all', methods=['GET'])
def api_analysis_export_all():
    """Generate and download all data (passwords + speedtest) as a single ZIP file."""
    current_user = get_current_user_id()
    if current_user == "0":
        return jsonify({"error": "User not authenticated"}), 401

    try:
        import zipfile
        import io
        
        analysis = Analysis(user_id=int(current_user))
        
        # Generate visualizations and get CSV files
        result = analysis.generate_visualizations()
        
        if result.get('error'):
            return jsonify({'error': result.get('error')}), 500
        
        csv_files = result.get('csv_files', [])
        report_file = result.get('report_file', '')
        
        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add CSV files
            for csv_file in csv_files:
                if os.path.exists(csv_file):
                    arcname = os.path.basename(csv_file)
                    zip_file.write(csv_file, arcname=arcname)
            
            # Add analysis report image
            if os.path.exists(report_file):
                arcname = os.path.basename(report_file)
                zip_file.write(report_file, arcname=arcname)
        
        zip_buffer.seek(0)
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'lifedesk_analysis_user_{current_user}.zip'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@Lifedesk.route("/api/analysis/report/<filename>", methods=["GET"])
def serve_analysis_report(filename):
    """Serve generated analysis report images"""
    current_user = get_current_user_id()
    if current_user == "0":
        return jsonify({"error": "User not authenticated"}), 401
    
    try:
        # Validate filename to prevent directory traversal
        if ".." in filename or "/" in filename:
            return jsonify({"error": "Invalid filename"}), 400
        
        # Only allow serving reports for current user
        if not filename.startswith(f"user_{current_user}"):
            return jsonify({"error": "Unauthorized"}), 403
        
        report_path = os.path.join("./analysis_reports", filename)
        if os.path.exists(report_path):
            return send_file(report_path, mimetype='image/png')
        else:
            return jsonify({"error": "Report not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":  
    Lifedesk.run(debug=True, host='localhost', port=5000)
  