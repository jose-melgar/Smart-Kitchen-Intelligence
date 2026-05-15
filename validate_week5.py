#!/usr/bin/env python3
"""
Validation script for Week 5 milestone
Checks for all required deliverables and structure
"""
import os
import json
from pathlib import Path
from datetime import datetime

class Week5Validator:
    def __init__(self, project_root="."):
        self.root = Path(project_root)
        self.report = {
            "timestamp": datetime.now().isoformat(),
            "status": "PENDING",
            "components": {},
            "errors": [],
            "warnings": []
        }
    
    def check_directory(self, path, name):
        """Check if directory exists"""
        full_path = self.root / path
        exists = full_path.exists() and full_path.is_dir()
        if not exists:
            self.report["errors"].append(f"Missing directory: {path}")
        return exists
    
    def check_file(self, path, name, critical=False):
        """Check if file exists"""
        full_path = self.root / path
        exists = full_path.exists() and full_path.is_file()
        if not exists:
            msg = f"Missing file: {path}"
            if critical:
                self.report["errors"].append(msg)
            else:
                self.report["warnings"].append(msg)
        return exists
    
    def check_python_script(self, script_path):
        """Check if Python script is valid"""
        full_path = self.root / script_path
        if not full_path.exists():
            self.report["errors"].append(f"Script not found: {script_path}")
            return False
        
        try:
            with open(full_path, 'r') as f:
                content = f.read()
            # Try to parse as Python
            compile(content, str(full_path), 'exec')
            return True
        except SyntaxError as e:
            self.report["errors"].append(f"Syntax error in {script_path}: {e}")
            return False
    
    def check_csv(self, csv_path):
        """Check if CSV is readable"""
        full_path = self.root / csv_path
        if not full_path.exists():
            return False, 0, 0
        
        try:
            import pandas as pd
            df = pd.read_csv(full_path, nrows=1)
            rows = sum(1 for _ in open(full_path)) - 1
            cols = len(df.columns)
            return True, rows, cols
        except Exception as e:
            self.report["warnings"].append(f"Error reading {csv_path}: {e}")
            return False, 0, 0
    
    def validate_week3_prerequisites(self):
        """Check Week 3 deliverables are complete"""
        print("\n📋 WEEK 3 PREREQUISITES CHECK")
        print("=" * 60)
        
        week3 = {
            "proposal": self.check_file("reports/proposal.md", "Project Proposal", critical=True),
            "source_inventory": self.check_file("reports/source_inventory.md", "Source Inventory", critical=True),
            "schema": self.check_file("reports/schema_draft.md", "Schema Draft", critical=True),
            "data_dict": self.check_file("reports/data_dictionary.md", "Data Dictionary", critical=True),
            "scale_analysis": self.check_file("reports/scale_analysis.md", "Scale Analysis", critical=True),
            "ethics_note": self.check_file("reports/ethics_note.md", "Ethics Note", critical=True),
            "processed_data": self.check_file("data/processed/inventory_v1.csv", "Processed Dataset V1", critical=True),
        }
        
        self.report["components"]["week3"] = {
            "status": "✅ COMPLETE" if all(week3.values()) else "❌ INCOMPLETE",
            "details": week3
        }
        
        for item, status in week3.items():
            print(f"  {'✅' if status else '❌'} {item.replace('_', ' ').title()}")
        
        return all(week3.values())
    
    def validate_feature_matrices(self):
        """Check for feature matrices"""
        print("\n📊 FEATURE MATRICES CHECK")
        print("=" * 60)
        
        features = {
            "numeric": self.check_file("data/features/numeric_features.csv", "Numeric Features"),
            "categorical": self.check_file("data/features/categorical_features.csv", "Categorical Features"),
            "text": self.check_file("data/features/text_features.csv", "Text Features"),
            "temporal": self.check_file("data/features/temporal_features.csv", "Temporal Features"),
            "combined": self.check_file("data/features/feature_matrix_combined.csv", "Combined Feature Matrix"),
        }
        
        # Check if at least main matrix exists
        has_features = any([features.get("combined"), features.get("numeric")])
        
        self.report["components"]["feature_matrices"] = {
            "status": "✅ PRESENT" if has_features else "⚠️ MISSING",
            "details": features
        }
        
        for ftype, exists in features.items():
            if exists:
                path = f"data/features/{ftype}_features.csv"
                exists_check, rows, cols = self.check_csv(path)
                print(f"  ✅ {ftype.title()}: {rows} rows × {cols} cols")
            else:
                print(f"  ⚠️ {ftype.title()}: Missing")
        
        return has_features
    
    def validate_dimensionality_reduction(self):
        """Check for dimensionality reduction analysis"""
        print("\n🔬 DIMENSIONALITY REDUCTION CHECK")
        print("=" * 60)
        
        reduction = {
            "script": self.check_python_script("src/reduction.py"),
            "pca_variance": self.check_file("artifacts/pca_explained_variance.csv", "PCA Variance"),
            "svd_variance": self.check_file("artifacts/svd_explained_variance.csv", "SVD Variance"),
            "comparison_table": self.check_file("artifacts/dimensionality_comparison.csv", "Comparison Table"),
            "pca_model": self.check_file("artifacts/pca_model.pkl", "PCA Model"),
            "scree_plot": self.check_file("reports/figures/scree_plot.png", "Scree Plot"),
            "pca_2d": self.check_file("reports/figures/pca_projection_2d.png", "PCA 2D Projection"),
            "tsne": self.check_file("reports/figures/tsne_visualization.png", "t-SNE Visualization"),
        }
        
        # Check core components
        has_core = reduction["script"] and (reduction["pca_variance"] or reduction["svd_variance"])
        
        self.report["components"]["dimensionality_reduction"] = {
            "status": "✅ IMPLEMENTED" if has_core else "❌ MISSING CORE",
            "details": reduction
        }
        
        print(f"  {'✅' if reduction['script'] else '❌'} reduction.py script")
        print(f"  {'✅' if reduction['pca_variance'] else '⚠️'} PCA analysis")
        print(f"  {'✅' if reduction['svd_variance'] else '⚠️'} SVD analysis")
        print(f"  {'✅' if reduction['comparison_table'] else '⚠️'} Comparison table")
        print(f"  {'✅' if reduction['scree_plot'] else '⚠️'} Scree plot")
        print(f"  {'✅' if reduction['pca_2d'] else '⚠️'} 2D projection")
        
        return has_core
    
    def validate_visualizations(self):
        """Check for required visualizations"""
        print("\n📈 VISUALIZATION CHECK")
        print("=" * 60)
        
        viz_dir = self.root / "reports/figures"
        self.check_directory("reports/figures", "Figures Directory")
        
        visualizations = {}
        required_plots = [
            "scree_plot.png",
            "pca_projection_2d.png",
            "feature_correlation_heatmap.png",
            "variance_explained_comparison.png"
        ]
        
        for plot in required_plots:
            path = f"reports/figures/{plot}"
            exists = self.check_file(path, plot, critical=False)
            visualizations[plot] = exists
            print(f"  {'✅' if exists else '⚠️'} {plot}")
        
        has_min_viz = sum(visualizations.values()) >= 2
        
        self.report["components"]["visualizations"] = {
            "status": "✅ SUFFICIENT" if has_min_viz else "⚠️ NEEDS MORE",
            "count": sum(visualizations.values()),
            "details": visualizations
        }
        
        return has_min_viz
    
    def validate_reporting(self):
        """Check for technical reports"""
        print("\n📝 REPORTING CHECK")
        print("=" * 60)
        
        reports = {
            "dimensionality_report": self.check_file("reports/dimensionality_report.md", "Dimensionality Report"),
            "interpretation": self.check_file("reports/feature_interpretation.md", "Technical Interpretation"),
            "runbook": self.check_file("runbook.md", "Runbook"),
        }
        
        self.report["components"]["reporting"] = {
            "status": "✅ PRESENT" if reports["dimensionality_report"] else "⚠️ INCOMPLETE",
            "details": reports
        }
        
        for report, exists in reports.items():
            print(f"  {'✅' if exists else '⚠️'} {report.replace('_', ' ').title()}")
        
        return reports["dimensionality_report"] is not None
    
    def validate_scripts(self):
        """Check all Python scripts are valid"""
        print("\n🔧 SCRIPT VALIDATION CHECK")
        print("=" * 60)
        
        scripts = {
            "ingestion.py": "src/ingestion.py",
            "preprocessing.py": "src/preprocessing.py",
            "features.py": "src/features.py",
            "reduction.py": "src/reduction.py",
        }
        
        results = {}
        for name, path in scripts.items():
            valid = self.check_python_script(path)
            results[name] = valid
            print(f"  {'✅' if valid else '❌'} {name}")
        
        self.report["components"]["scripts"] = {
            "status": "✅ VALID" if all(results.values()) else "⚠️ ERRORS",
            "details": results
        }
        
        return all(results.values())
    
    def validate_reproducibility(self):
        """Check reproducibility elements"""
        print("\n🔄 REPRODUCIBILITY CHECK")
        print("=" * 60)
        
        reproducible = {
            "requirements.txt": self.check_file("requirements.txt", "Requirements"),
            "pyproject.toml": self.check_file("pyproject.toml", "PyProject"),
            "runbook": self.check_file("runbook.md", "Runbook"),
            "data_version": self.check_file("data/processed/inventory_v1.csv", "Versioned Data"),
        }
        
        self.report["components"]["reproducibility"] = {
            "status": "✅ GOOD" if reproducible["requirements.txt"] else "⚠️ MISSING DEPS",
            "details": reproducible
        }
        
        for item, exists in reproducible.items():
            print(f"  {'✅' if exists else '⚠️'} {item.replace('_', ' ').title()}")
        
        return reproducible["requirements.txt"]
    
    def generate_summary(self):
        """Generate validation summary"""
        print("\n" + "=" * 60)
        print("📊 VALIDATION SUMMARY")
        print("=" * 60)
        
        total_components = len(self.report["components"])
        errors = len(self.report["errors"])
        warnings = len(self.report["warnings"])
        
        print(f"\n✅ COMPONENTS CHECKED: {total_components}")
        print(f"❌ CRITICAL ERRORS: {errors}")
        print(f"⚠️ WARNINGS: {warnings}")
        
        if errors == 0:
            self.report["status"] = "✅ READY FOR WEEK 5"
        elif errors < 3:
            self.report["status"] = "⚠️ MOSTLY READY - FIX ERRORS"
        else:
            self.report["status"] = "❌ NOT READY - NEEDS WORK"
        
        print(f"\n🎯 OVERALL STATUS: {self.report['status']}")
        
        if self.report["errors"]:
            print("\n❌ CRITICAL ISSUES:")
            for error in self.report["errors"]:
                print(f"   - {error}")
        
        if self.report["warnings"]:
            print("\n⚠️ RECOMMENDATIONS:")
            for warning in self.report["warnings"][:5]:
                print(f"   - {warning}")
    
    def run(self):
        """Run full validation"""
        print("\n" + "=" * 60)
        print("🔍 WEEK 5 PROJECT VALIDATION")
        print("=" * 60)
        print(f"Project Root: {self.root}")
        print(f"Current Branch: Gabriel")
        
        # Run all checks
        self.validate_week3_prerequisites()
        self.validate_feature_matrices()
        self.validate_dimensionality_reduction()
        self.validate_visualizations()
        self.validate_reporting()
        self.validate_scripts()
        self.validate_reproducibility()
        
        # Generate summary
        self.generate_summary()
        
        return self.report

if __name__ == "__main__":
    validator = Week5Validator()
    report = validator.run()
    
    # Save report
    report_path = Path("artifacts/validation_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n💾 Report saved to: {report_path}")
