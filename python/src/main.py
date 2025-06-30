import json
import os
import sys
import subprocess
from typing import Dict, Any
from document_extractor import DocumentExtractor
from claude_comparator import SemanticClaudeComparator
from report_generator import SemanticReportGenerator
from datetime import datetime

# Import the new download manager
try:
    from download_reports import ReportsDownloadManager
except ImportError:
    print("⚠️ Download manager not found. Download features will be disabled.")
    ReportsDownloadManager = None


class SemanticQualityTestOrchestrator:
    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.extractor = DocumentExtractor()
        self.comparator = SemanticClaudeComparator()
        self.reporter = SemanticReportGenerator()
        
        # Initialize download manager if available
        if ReportsDownloadManager:
            self.download_manager = ReportsDownloadManager()
        else:
            self.download_manager = None
        
        # Ensure directories exist
        os.makedirs('data/source_files', exist_ok=True)
        os.makedirs('data/ai_outputs', exist_ok=True)
        os.makedirs('data/extracted', exist_ok=True)
        os.makedirs('data/reports', exist_ok=True)
        os.makedirs('downloads', exist_ok=True)  # For download packages
    
    def run_frontend_extraction(self):
        """NEW: Run Cypress verified recordsS data extraction"""
        print("🌐 STEP 1: VERIFIED RECORDS DATA EXTRACTION")
        print("="*50)
        
        try:
            # Check if Cypress is available
            result = subprocess.run(["npx", "cypress", "version"], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                print("⚠️ Cypress not found. Please install: npm install cypress")
                return False
            
            print("🚀 Running Cypress frontend data extraction...")
            
            # Run Cypress extraction
            cmd = [
                "npx", "cypress", "run", 
                "--spec", "cypress/e2e/data_extraction.cy.js",
                "--headless",
                "--browser", "chrome"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print("✅ Cypress extraction completed successfully!")
                self.verify_frontend_data()
                return True
            else:
                print("❌ Cypress extraction failed:")
                print("STDOUT:", result.stdout[-500:])  # Last 500 chars
                print("STDERR:", result.stderr[-500:])
                print("\n⚠️ Continuing with existing frontend data (if any)...")
                return False
                
        except subprocess.TimeoutExpired:
            print("⏰ Cypress extraction timed out (5 minutes)")
            print("⚠️ Continuing with existing frontend data (if any)...")
            return False
        except FileNotFoundError:
            print("❌ Node.js/npm not found. Please install Node.js")
            print("⚠️ Continuing with existing frontend data (if any)...")
            return False
        except Exception as e:
            print(f"❌ Error running Cypress: {e}")
            print("⚠️ Continuing with existing frontend data (if any)...")
            return False
    
    def verify_frontend_data(self):
        """Verify that frontend data was extracted successfully"""
        print("\n📊 Verifying frontend data extraction...")
        
        companies = self.config.get('companies', [])
        extracted_count = 0
        
        for company in companies:
            company_name = company['name']
            frontend_file = f"data/extracted/{company_name}_frontend_data.json"
            
            if os.path.exists(frontend_file):
                try:
                    with open(frontend_file, 'r') as f:
                        data = json.load(f)
                    
                    # Count non-empty fields
                    non_empty_fields = sum(1 for k, v in data.items() 
                                         if not k.startswith('_') and v and v != 'N/A' and str(v).strip())
                    
                    print(f"      ✅ {company_name}: {non_empty_fields} fields extracted")
                    extracted_count += 1
                    
                except Exception as e:
                    print(f"      ❌ {company_name}: Error reading frontend data - {e}")
            else:
                print(f"      ❌ {company_name}: No frontend data file found")
        
        total_companies = len(companies)
        print(f"\n📈 Frontend Data Summary: {extracted_count}/{total_companies} companies extracted")
        
        if extracted_count == 0:
            print("⚠️ WARNING: No frontend data found!")
            print("💡 Make sure your Cypress script is working and saving data to data/extracted/")
        
        return extracted_count > 0
    
    def validate_data_extraction(self, company_name: str) -> bool:
        """Validate that data extraction worked properly"""
        frontend_file = f"data/extracted/{company_name}_frontend_data.json"
        
        if not os.path.exists(frontend_file):
            print(f"      ❌ Frontend data file not found: {frontend_file}")
            return False
        
        try:
            with open(frontend_file, 'r') as f:
                data = json.load(f)
            
            # Check if data has actual values (not all N/A)
            non_empty_fields = sum(1 for k, v in data.items() 
                                 if not k.startswith('_') and v and v != 'N/A' and str(v).strip())
            
            print(f"      📊 Frontend data validation: {non_empty_fields} fields with data")
            
            if non_empty_fields == 0:
                print(f"      ⚠️ Warning: No data extracted from frontend")
                return False
            
            return True
            
        except Exception as e:
            print(f"      ❌ Error reading frontend data: {e}")
            return False
    
    def process_company_semantic(self, company_config: Dict) -> Dict[str, Any]:
        """Process company with semantic matching"""
        company_name = company_config['name']
        print(f"\n{'='*60}")
        print(f"🧠 Semantic Processing: {company_name}")
        print(f"{'='*60}")
        
        # Extract documents
        print("2️⃣ Extracting source documents...")
        doc_data = self.extractor.process_company_documents(company_config)
        
        source_text = doc_data.get('combined_source_text', '')
        if not source_text:
            print(f"❌ No source text available for {company_name}")
            return {}
        
        # Validate frontend data extraction
        print("3️⃣ Validating frontend data extraction...")
        if not self.validate_data_extraction(company_name):
            print(f"⚠️ Proceeding with limited data for {company_name}")
        
        # Load frontend data
        frontend_data = {}
        frontend_file = f"data/extracted/{company_name}_frontend_data.json"
        if os.path.exists(frontend_file):
            with open(frontend_file, 'r') as f:
                frontend_data = json.load(f)
        
        # Get AI memo data
        ai_memo = doc_data.get('ai_generated_memo', {})
        
        print(f"📊 Data Summary:")
        print(f"   📁 Source text: {len(source_text):,} characters")
        print(f"   🌐 Frontend fields: {len(frontend_data)} total")
        print(f"   📋 AI memo sections: {len([s for s in ai_memo.get('memo_sections', {}).values() if s.strip()])} with content")
        
        # Semantic comparison of frontend data
        print("4️⃣ Semantic comparison: Frontend vs Source")
        frontend_results = {}
        if frontend_data:
            frontend_results = self.comparator.batch_compare_frontend_semantic(
                frontend_data,
                source_text,
                self.config['frontend_fields']
            )
        
        # Semantic comparison of memo sections
        print("5️⃣ Semantic comparison: Memo vs Source")
        memo_results = {}
        if ai_memo.get('memo_sections'):
            memo_results = self.comparator.batch_compare_memo_semantic(
                ai_memo['memo_sections'],
                source_text,
                self.config['pdf_sections']
            )
        
        # Generate semantic report
        print("6️⃣ Generating semantic quality report...")
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = f"data/reports/{company_name}_semantic_report_{timestamp}.pdf"
        
        self.reporter.create_semantic_quality_report(
            company_name,
            frontend_results,
            memo_results,
            report_path
        )
        
        # Calculate scores
        frontend_avg = sum(r.get('accuracy_score', 0) for r in frontend_results.values()) / len(frontend_results) if frontend_results else 0
        memo_avg = sum(r.get('accuracy_score', 0) for r in memo_results.values()) / len(memo_results) if memo_results else 0
        overall_avg = (frontend_avg + memo_avg) / 2 if (frontend_results or memo_results) else 0
        
        print(f"📈 Semantic Results:")
        print(f"   🌐 Frontend: {frontend_avg:.1f}/100")
        print(f"   📋 Memo: {memo_avg:.1f}/100")
        print(f"   🎯 Overall: {overall_avg:.1f}/100")
        print(f"   📄 Report: {os.path.basename(report_path)}")
        
        return {
            'frontend_results': frontend_results,
            'memo_results': memo_results,
            'frontend_avg_score': frontend_avg,
            'memo_avg_score': memo_avg,
            'overall_score': overall_avg,
            'report_path': report_path
        }
    
    def create_download_package(self):
        """Create a downloadable package of all reports"""
        if not self.download_manager:
            print("❌ Download manager not available")
            return None
        
        print("\n📦 CREATING DOWNLOAD PACKAGE")
        print("="*50)
        
        zip_path = self.download_manager.create_reports_zip()
        
        if zip_path:
            print(f"\n✅ Download package ready!")
            print(f"📁 You can download: {os.path.abspath(zip_path)}")
            print(f"💡 This package contains all your PDF reports and metadata")
            
            # Clean up old packages
            self.download_manager.clean_old_downloads()
            
        return zip_path
    
    def run_semantic_assessment(self):
        """Run complete semantic assessment with integrated frontend extraction"""
        print("🧠 AI SEMANTIC QUALITY ASSESSMENT - INTEGRATED WORKFLOW")
        print("="*60)
        print("🎯 WORKFLOW: VERIFIED RECORDS Extraction → Quality Assessment → PDF Reports → Download Package")
        print("="*60)
        
        # NEW: Step 1 - Run frontend extraction first
        frontend_success = self.run_frontend_extraction()
        
        if not frontend_success:
            print("\n⚠️ Frontend extraction had issues, but continuing with assessment...")
            print("💡 The system will use any existing frontend data files")
        
        # Step 2 - Continue with quality assessment
        print("\n🧠 STEP 2: AI QUALITY ASSESSMENT")
        print("="*50)
        
        all_results = {}
        
        for i, company in enumerate(self.config['companies'], 1):
            print(f"\n[{i}/{len(self.config['companies'])}] Processing {company['name']}...")
            
            try:
                result = self.process_company_semantic(company)
                if result:
                    all_results[company['name']] = result
                    
            except Exception as e:
                print(f"❌ Error processing {company['name']}: {e}")
                import traceback
                traceback.print_exc()
        
        # Generate summary report
        if all_results:
            print(f"\n📊 Generating semantic summary report...")
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            summary_path = f"data/reports/semantic_summary_{timestamp}.pdf"
            
            self.reporter.create_summary_report(all_results, summary_path)
            
            print(f"\n✅ INTEGRATED WORKFLOW COMPLETED!")
            print("="*60)
            print(f"📈 RESULTS:")
            
            for company_name, results in all_results.items():
                overall_score = results.get('overall_score', 0)
                status = "✅ PASS" if overall_score >= 70 else "❌ FAIL"
                print(f"   {company_name}: {overall_score:.1f}/100 {status}")
            
            total_avg = sum(r.get('overall_score', 0) for r in all_results.values()) / len(all_results)
            print(f"\n🎯 Average Score: {total_avg:.1f}/100")
            print(f"📊 Summary Report: {os.path.basename(summary_path)}")
            print(f"📁 Full Path: {os.path.abspath(summary_path)}")
            
            # NEW: Step 3 - Create download package
            print(f"\n📦 STEP 3: CREATING DOWNLOAD PACKAGE")
            print("="*50)
            
            zip_path = self.create_download_package()
            
            print(f"\n🎉 WORKFLOW COMPLETE!")
            print("✅ Frontend data extracted")
            print("✅ Quality assessment completed")
            print("✅ PDF reports generated")
            if zip_path:
                print("✅ Download package created")
            
        else:
            print("\n❌ No results generated - check your configuration and data files")

def show_help():
    """Show help information"""
    print("""
🧠 AI SEMANTIC QUALITY ASSESSMENT TOOL
=====================================

Usage: python main.py [OPTIONS]

OPTIONS:
  (none)              Run complete workflow (default)
  --skip-frontend     Skip frontend extraction, use existing data
  --download-only     Only create download package from existing reports
  --list-downloads    List available download packages
  --help, -h          Show this help message

EXAMPLES:
  python main.py                    # Full workflow
  python main.py --skip-frontend   # Skip frontend extraction
  python main.py --download-only   # Create download package only
  python main.py --list-downloads  # List available downloads

WORKFLOW:
1. Frontend Data Extraction (Cypress)
2. AI Quality Assessment (Semantic Matching)
3. PDF Report Generation
4. Download Package Creation
""")

def main():
    if not os.path.exists('config.json'):
        print("❌ config.json not found!")
        return
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        
        if arg in ['--help', '-h']:
            show_help()
            return
        
        elif arg == "--skip-frontend":
            print("⏭️ Skipping frontend extraction (using existing data)")
            # Create orchestrator but skip frontend extraction
            orchestrator = SemanticQualityTestOrchestrator('config.json')
            # Skip to quality assessment
            print("🧠 STEP 2: AI QUALITY ASSESSMENT")
            print("="*50)
            all_results = {}
            
            for i, company in enumerate(orchestrator.config['companies'], 1):
                print(f"\n[{i}/{len(orchestrator.config['companies'])}] Processing {company['name']}...")
                
                try:
                    result = orchestrator.process_company_semantic(company)
                    if result:
                        all_results[company['name']] = result
                        
                except Exception as e:
                    print(f"❌ Error processing {company['name']}: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Generate summary report
            if all_results:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                summary_path = f"data/reports/semantic_summary_{timestamp}.pdf"
                orchestrator.reporter.create_summary_report(all_results, summary_path)
                
                # Create download package
                orchestrator.create_download_package()
                
                print(f"\n✅ Quality assessment completed (frontend extraction skipped)")
            
            return
        
        elif arg == "--download-only":
            print("📦 Creating download package only...")
            orchestrator = SemanticQualityTestOrchestrator('config.json')
            zip_path = orchestrator.create_download_package()
            if not zip_path:
                print("❌ No reports found to package")
            return
        
        elif arg == "--list-downloads":
            print("📦 Listing available download packages...")
            if ReportsDownloadManager:
                download_manager = ReportsDownloadManager()
                download_manager.list_available_downloads()
            else:
                print("❌ Download manager not available")
            return
        
        else:
            print(f"❌ Unknown argument: {arg}")
            print("Use --help for usage information")
            return
    
    # Default: Run full workflow
    try:
        orchestrator = SemanticQualityTestOrchestrator('config.json')
        orchestrator.run_semantic_assessment()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()