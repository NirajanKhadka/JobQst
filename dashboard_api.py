#!/usr/bin/env python3
"""
Dashboard Data API - Test and Debug Tool
Creates a simple API to inspect what data the dashboard sees
"""

from flask import Flask, jsonify
from flask_cors import CORS
import sys
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent))

app = Flask(__name__)
CORS(app)

@app.route('/api/profiles', methods=['GET'])
def get_profiles():
    """List all available profiles"""
    try:
        from src.core.user_profile_manager import UserProfileManager
        pm = UserProfileManager()
        profiles = pm.list_profiles()
        return jsonify({
            "success": True,
            "profiles": profiles,
            "count": len(profiles)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/profile/<profile_name>', methods=['GET'])
def get_profile(profile_name):
    """Get profile details"""
    try:
        from src.utils.profile_helpers import load_profile
        profile = load_profile(profile_name)
        if profile:
            return jsonify({
                "success": True,
                "profile": profile
            })
        return jsonify({"success": False, "error": "Profile not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/jobs/<profile_name>', methods=['GET'])
def get_jobs(profile_name):
    """Get jobs from database"""
    try:
        from src.core.duckdb_database import DuckDBJobDatabase
        
        db = DuckDBJobDatabase(profile_name=profile_name)
        
        # Get count
        count_result = db.conn.execute("SELECT COUNT(*) as count FROM jobs").fetchone()
        count = count_result[0] if count_result else 0
        
        # Get sample jobs
        jobs_df = db.conn.execute("""
            SELECT id, title, company, location, fit_score, date_posted, profile_name
            FROM jobs 
            LIMIT 10
        """).df()
        
        jobs_list = jobs_df.to_dict('records') if not jobs_df.empty else []
        
        return jsonify({
            "success": True,
            "profile": profile_name,
            "total_jobs": count,
            "sample_jobs": jobs_list,
            "database_path": str(db.db_file)
        })
    except Exception as e:
        import traceback
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@app.route('/api/data-loader/<profile_name>', methods=['GET'])
def test_data_loader(profile_name):
    """Test DataLoader (what dashboard uses)"""
    try:
        from src.dashboard.dash_app.utils.data_loader import DataLoader
        
        dl = DataLoader()
        df = dl.load_jobs_data(profile_name)
        
        return jsonify({
            "success": True,
            "profile": profile_name,
            "jobs_loaded": len(df),
            "columns": list(df.columns) if not df.empty else [],
            "sample": df.head(5).to_dict('records') if not df.empty else []
        })
    except Exception as e:
        import traceback
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@app.route('/api/database-files/<profile_name>', methods=['GET'])
def check_database_files(profile_name):
    """Check what database files exist"""
    try:
        profile_dir = Path(f"profiles/{profile_name}")
        
        if not profile_dir.exists():
            return jsonify({
                "success": False,
                "error": f"Profile directory not found: {profile_dir}"
            }), 404
        
        # Find all database files
        db_files = []
        for pattern in ['*.db', '*.duckdb']:
            db_files.extend(profile_dir.glob(pattern))
        
        files_info = []
        for db_file in db_files:
            files_info.append({
                "name": db_file.name,
                "path": str(db_file),
                "size": db_file.stat().st_size,
                "exists": db_file.exists()
            })
        
        return jsonify({
            "success": True,
            "profile": profile_name,
            "profile_dir": str(profile_dir),
            "database_files": files_info
        })
    except Exception as e:
        import traceback
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@app.route('/api/fix-database/<profile_name>', methods=['POST'])
def fix_database_naming(profile_name):
    """Fix database file naming issues"""
    try:
        import shutil
        profile_dir = Path(f"profiles/{profile_name}")
        
        # Check for case variations
        variations = [
            f"{profile_name}_duckdb.db",
            f"{profile_name.lower()}_duckdb.db",
            f"{profile_name.title()}_duckdb.db",
            f"{profile_name}_DUCKDB.db",
        ]
        
        found_files = []
        for var in variations:
            db_path = profile_dir / var
            if db_path.exists():
                found_files.append(str(db_path))
        
        if not found_files:
            return jsonify({
                "success": False,
                "error": "No database files found"
            }), 404
        
        # Use the first found file
        source_file = Path(found_files[0])
        
        # Create standardized name (lowercase)
        standard_name = f"{profile_name.lower()}_duckdb.db"
        target_file = profile_dir / standard_name
        
        if source_file != target_file:
            shutil.copy2(source_file, target_file)
            operation = f"Copied {source_file.name} to {target_file.name}"
        else:
            operation = "Database already has correct name"
        
        return jsonify({
            "success": True,
            "operation": operation,
            "source": str(source_file),
            "target": str(target_file),
            "found_files": found_files
        })
    except Exception as e:
        import traceback
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@app.route('/', methods=['GET'])
def index():
    """API documentation"""
    return jsonify({
        "name": "JobLens Dashboard Data API",
        "version": "1.0.0",
        "endpoints": {
            "/api/profiles": "List all profiles",
            "/api/profile/<name>": "Get profile details",
            "/api/jobs/<name>": "Get jobs from database (direct query)",
            "/api/data-loader/<name>": "Test DataLoader (what dashboard uses)",
            "/api/database-files/<name>": "Check database files",
            "/api/fix-database/<name>": "Fix database naming (POST)"
        },
        "examples": {
            "profiles": "/api/profiles",
            "nirajan_jobs": "/api/jobs/Nirajan",
            "demo_jobs": "/api/jobs/Demo",
            "nirajan_dataloader": "/api/data-loader/Nirajan",
            "check_files": "/api/database-files/Nirajan"
        }
    })


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🔥 JobLens Dashboard Data API - TANDAVA MODE 🔥")
    print("="*60)
    print("\nAPI Endpoints:")
    print("  http://localhost:5000/                     - API docs")
    print("  http://localhost:5000/api/profiles         - List profiles")
    print("  http://localhost:5000/api/jobs/Nirajan     - Get Nirajan jobs")
    print("  http://localhost:5000/api/data-loader/Nirajan - Test DataLoader")
    print("  http://localhost:5000/api/database-files/Nirajan - Check DB files")
    print("\n" + "="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
