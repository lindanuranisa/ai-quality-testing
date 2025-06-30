import os
import zipfile
import shutil
from datetime import datetime
import json
from typing import List, Dict
import glob

class ReportsDownloadManager:
    def __init__(self, reports_dir: str = "data/reports"):
        self.reports_dir = reports_dir
        self.downloads_dir = "downloads"
        
        # Ensure directories exist
        os.makedirs(self.reports_dir, exist_ok=True)
        os.makedirs(self.downloads_dir, exist_ok=True)
    
    def get_all_report_files(self) -> List[str]:
        """Get all report files from the reports directory"""
        if not os.path.exists(self.reports_dir):
            print(f"❌ Reports directory not found: {self.reports_dir}")
            return []
        
        # Find all PDF files in reports directory
        pdf_files = glob.glob(os.path.join(self.reports_dir, "*.pdf"))
        
        if not pdf_files:
            print(f"⚠️ No PDF reports found in {self.reports_dir}")
            return []
        
        # Sort by modification time (newest first)
        pdf_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        
        print(f"📄 Found {len(pdf_files)} report files:")
        for i, file_path in enumerate(pdf_files, 1):
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            print(f"   {i}. {file_name} ({file_size:.1f} MB) - {mod_time.strftime('%Y-%m-%d %H:%M')}")
        
        return pdf_files
    
    def create_reports_zip(self, include_metadata: bool = True) -> str:
        """Create a zip file with all reports"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = f"AI_Quality_Reports_{timestamp}.zip"
        zip_path = os.path.join(self.downloads_dir, zip_filename)
        
        report_files = self.get_all_report_files()
        
        if not report_files:
            print("❌ No reports to package")
            return None
        
        print(f"\n📦 Creating download package: {zip_filename}")
        
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add all report files
                for file_path in report_files:
                    file_name = os.path.basename(file_path)
                    zipf.write(file_path, file_name)
                    print(f"   ✅ Added: {file_name}")
                
                # Add metadata if requested
                if include_metadata:
                    metadata = self.generate_metadata(report_files)
                    metadata_json = json.dumps(metadata, indent=2)
                    zipf.writestr("reports_metadata.json", metadata_json)
                    print(f"   ✅ Added: reports_metadata.json")
                    
                    # Create a readable summary
                    summary_text = self.generate_summary_text(metadata)
                    zipf.writestr("REPORTS_SUMMARY.txt", summary_text)
                    print(f"   ✅ Added: REPORTS_SUMMARY.txt")
            
            # Get final zip size
            zip_size = os.path.getsize(zip_path) / (1024 * 1024)  # MB
            
            print(f"\n🎉 Download package created successfully!")
            print(f"📁 Location: {os.path.abspath(zip_path)}")
            print(f"📊 Package size: {zip_size:.1f} MB")
            print(f"📄 Contains: {len(report_files)} report files")
            
            return zip_path
            
        except Exception as e:
            print(f"❌ Error creating zip file: {e}")
            return None
    
    def generate_metadata(self, report_files: List[str]) -> Dict:
        """Generate metadata for the reports"""
        metadata = {
            "package_info": {
                "created_at": datetime.now().isoformat(),
                "total_reports": len(report_files),
                "package_type": "AI Quality Assessment Reports"
            },
            "reports": []
        }
        
        for file_path in report_files:
            file_name = os.path.basename(file_path)
            file_stats = os.stat(file_path)
            
            # Parse report type from filename
            report_type = "unknown"
            company_name = "unknown"
            
            if "semantic_report" in file_name:
                report_type = "individual_assessment"
                company_name = file_name.split("_semantic_report")[0]
            elif "semantic_summary" in file_name:
                report_type = "summary_report"
                company_name = "all_companies"
            
            report_info = {
                "filename": file_name,
                "report_type": report_type,
                "company_name": company_name,
                "file_size_mb": round(file_stats.st_size / (1024 * 1024), 2),
                "created_at": datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(file_stats.st_mtime).isoformat()
            }
            
            metadata["reports"].append(report_info)
        
        return metadata
    
    def generate_summary_text(self, metadata: Dict) -> str:
        """Generate a human-readable summary"""
        summary = f"""AI QUALITY ASSESSMENT REPORTS - DOWNLOAD PACKAGE
{'='*60}

Package Information:
- Created: {metadata['package_info']['created_at']}
- Total Reports: {metadata['package_info']['total_reports']}
- Package Type: {metadata['package_info']['package_type']}

Report Files:
{'='*60}
"""
        
        # Group reports by type
        individual_reports = [r for r in metadata['reports'] if r['report_type'] == 'individual_assessment']
        summary_reports = [r for r in metadata['reports'] if r['report_type'] == 'summary_report']
        
        if summary_reports:
            summary += f"\n📊 SUMMARY REPORTS ({len(summary_reports)}):\n"
            for report in summary_reports:
                summary += f"   • {report['filename']} ({report['file_size_mb']} MB)\n"
        
        if individual_reports:
            summary += f"\n🏢 INDIVIDUAL COMPANY REPORTS ({len(individual_reports)}):\n"
            for report in individual_reports:
                summary += f"   • {report['company_name']}: {report['filename']} ({report['file_size_mb']} MB)\n"
        
        summary += f"\n\nHow to Use These Reports:\n"
        summary += f"{'='*60}\n"
        summary += f"1. Summary Reports: Overall assessment across all companies\n"
        summary += f"2. Individual Reports: Detailed analysis for each company\n"
        summary += f"3. reports_metadata.json: Machine-readable metadata\n"
        summary += f"\nAll reports are in PDF format and can be opened with any PDF viewer.\n"
        
        return summary
    
    def clean_old_downloads(self, keep_latest: int = 5):
        """Clean up old download packages"""
        if not os.path.exists(self.downloads_dir):
            return
        
        # Find all zip files in downloads directory
        zip_files = glob.glob(os.path.join(self.downloads_dir, "AI_Quality_Reports_*.zip"))
        
        if len(zip_files) <= keep_latest:
            return
        
        # Sort by modification time (oldest first)
        zip_files.sort(key=lambda x: os.path.getmtime(x))
        
        # Remove oldest files
        files_to_remove = zip_files[:-keep_latest]
        
        print(f"\n🧹 Cleaning up old download packages...")
        for file_path in files_to_remove:
            try:
                os.remove(file_path)
                print(f"   🗑️ Removed: {os.path.basename(file_path)}")
            except Exception as e:
                print(f"   ⚠️ Could not remove {os.path.basename(file_path)}: {e}")
    
    def list_available_downloads(self):
        """List all available download packages"""
        if not os.path.exists(self.downloads_dir):
            print("📁 No downloads directory found")
            return
        
        zip_files = glob.glob(os.path.join(self.downloads_dir, "AI_Quality_Reports_*.zip"))
        
        if not zip_files:
            print("📦 No download packages found")
            return
        
        zip_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        
        print(f"📦 Available Download Packages:")
        print(f"{'='*60}")
        
        for i, file_path in enumerate(zip_files, 1):
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            
            print(f"{i}. {file_name}")
            print(f"   📊 Size: {file_size:.1f} MB")
            print(f"   📅 Created: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   📁 Path: {os.path.abspath(file_path)}")
            print()

def main():
    """Command-line interface for report downloads"""
    import sys
    
    download_manager = ReportsDownloadManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "create":
            print("🚀 Creating download package...")
            zip_path = download_manager.create_reports_zip()
            if zip_path:
                download_manager.clean_old_downloads()
                
        elif command == "list":
            download_manager.list_available_downloads()
            
        elif command == "clean":
            keep_count = int(sys.argv[2]) if len(sys.argv) > 2 else 3
            download_manager.clean_old_downloads(keep_count)
            
        else:
            print("❌ Unknown command. Use: create, list, or clean")
    else:
        # Interactive mode
        print("📦 AI Quality Reports Download Manager")
        print("="*50)
        print("1. Create download package")
        print("2. List available packages") 
        print("3. Clean old packages")
        print("4. Exit")
        
        while True:
            choice = input("\nSelect option (1-4): ").strip()
            
            if choice == "1":
                print("\n🚀 Creating download package...")
                zip_path = download_manager.create_reports_zip()
                if zip_path:
                    download_manager.clean_old_downloads()
                break
                
            elif choice == "2":
                print()
                download_manager.list_available_downloads()
                
            elif choice == "3":
                keep = input("How many recent packages to keep? (default: 3): ").strip()
                keep_count = int(keep) if keep.isdigit() else 3
                download_manager.clean_old_downloads(keep_count)
                
            elif choice == "4":
                print("👋 Goodbye!")
                break
                
            else:
                print("❌ Invalid choice. Please select 1-4.")

if __name__ == "__main__":
    main()