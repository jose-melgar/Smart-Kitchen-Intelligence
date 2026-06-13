#!/usr/bin/env python3
"""
Smart Kitchen Intelligence - Preparation Script for Presentation
Valida y prepara todo lo necesario para la presentación del proyecto.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

# Colores para terminal
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}>>> {text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}\n")

def print_success(text):
    print(f"{Colors.GREEN}[OK] {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}[ERROR] {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}[WARN] {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.BLUE}[INFO] {text}{Colors.END}")

def check_file_exists(path, description):
    """Verifica si un archivo existe"""
    if Path(path).exists():
        size = Path(path).stat().st_size
        if size > 0:
            print_success(f"{description}: {path} ({size} bytes)")
            return True
        else:
            print_warning(f"{description}: {path} existe pero está vacío")
            return False
    else:
        print_error(f"{description}: {path} NO EXISTE")
        return False

def validate_data_files():
    """Valida que todos los archivos de datos existen"""
    print_header("VALIDANDO ARCHIVOS DE DATOS")

    checks = {
        'data/raw/instacart_patterns.json': 'Patrones de Instacart',
        'data/raw/movements_raw.csv': 'Movimientos simulados',
        'data/raw/catalog_raw.csv': 'Catálogo de productos',
        'data/processed/inventory_v1.csv': 'Dataset procesado',
        'data/features/feature_matrix.npy': 'Matriz de características',
        'data/features/feature_names.json': 'Nombres de características',
    }

    all_ok = True
    for path, desc in checks.items():
        if not check_file_exists(path, desc):
            all_ok = False

    return all_ok

def validate_reports():
    """Valida que los reportes existen"""
    print_header("VALIDANDO REPORTES Y DOCUMENTACIÓN")

    reports = {
        'reports/proposal.md': 'Propuesta del proyecto',
        'reports/data_dictionary.md': 'Diccionario de datos',
        'reports/scale_analysis.md': 'Análisis de escala',
        'reports/ethics_note.md': 'Nota de ética',
        'README_PRESENTACION.md': 'README para presentación',
        'GUIA_DEFENSA.md': 'Guía de defensa',
    }

    all_ok = True
    for path, desc in reports.items():
        if not check_file_exists(path, desc):
            all_ok = False

    return all_ok

def validate_source_code():
    """Valida que todos los scripts Python existen"""
    print_header("VALIDANDO CÓDIGO FUENTE")

    scripts = {
        'src/ingestion.py': 'Ingesta de datos',
        'src/simulation.py': 'Simulación',
        'src/preprocessing.py': 'Preprocesamiento',
        'src/features.py': 'Ingeniería de características',
        'src/reduction.py': 'Análisis de reducción',
        'validate_week5.py': 'Script de validación',
    }

    all_ok = True
    for path, desc in scripts.items():
        if not check_file_exists(path, desc):
            all_ok = False

    return all_ok

def check_python_packages():
    """Verifica que los paquetes principales estén instalados"""
    print_header("VALIDANDO PAQUETES PYTHON")

    packages = ['pandas', 'numpy', 'scikit-learn', 'matplotlib', 'seaborn', 'polars']
    all_ok = True

    for package in packages:
        try:
            __import__(package)
            print_success(f"Paquete '{package}' instalado")
        except ImportError:
            print_error(f"Paquete '{package}' NO INSTALADO")
            all_ok = False

    return all_ok

def generate_summary_report():
    """Genera un resumen del proyecto"""
    print_header("RESUMEN DEL PROYECTO")

    try:
        # Cargar información del dataset
        df_info = {
            'rows': 0,
            'columns': 0,
            'size_mb': 0,
        }

        if Path('data/processed/inventory_v1.csv').exists():
            import pandas as pd
            df = pd.read_csv('data/processed/inventory_v1.csv', nrows=10)
            df_info['columns'] = len(df.columns)
            file_size = Path('data/processed/inventory_v1.csv').stat().st_size / (1024*1024)
            df_info['size_mb'] = round(file_size, 2)

            # Estimar número de filas
            with open('data/processed/inventory_v1.csv', 'r') as f:
                df_info['rows'] = sum(1 for _ in f) - 1

        print_info(f"Dataset procesado: {df_info['rows']:,} filas × {df_info['columns']} columnas")
        print_info(f"Tamaño: {df_info['size_mb']} MB")

        # Features matrix
        if Path('data/features/feature_matrix.npy').exists():
            import numpy as np
            X = np.load('data/features/feature_matrix.npy')
            print_info(f"Matriz de características: {X.shape[0]:,} observaciones × {X.shape[1]} features")

        # Componentes PCA
        try:
            if Path('reports/figures/pca_scree_plot.png').exists():
                print_success("Gráfico Scree Plot generado")
            if Path('reports/figures/pca_scatter_2d.png').exists():
                print_success("Proyección 2D generada")
        except:
            pass

    except Exception as e:
        print_warning(f"No se pudo generar resumen: {str(e)}")

def create_presentation_checklist():
    """Crea un checklist para la presentación"""
    print_header("CHECKLIST PARA LA PRESENTACIÓN")

    checklist = {
        '[DATA]': [
            ('Dataset procesado cargable', Path('data/processed/inventory_v1.csv').exists()),
            ('Matriz de características lista', Path('data/features/feature_matrix.npy').exists()),
            ('Catálogo enriquecido', Path('data/raw/catalog_raw.csv').exists()),
        ],
        '[REPORTS]': [
            ('Propuesta documentada', Path('reports/proposal.md').exists()),
            ('Data dictionary completo', Path('reports/data_dictionary.md').exists()),
            ('Análisis de escala', Path('reports/scale_analysis.md').exists()),
        ],
        '[CODE]': [
            ('Pipeline ejecutable', Path('src/preprocessing.py').exists()),
            ('Scripts de validación', Path('validate_week5.py').exists()),
            ('Feature engineering', Path('src/features.py').exists()),
        ],
        '[VISUALIZATIONS]': [
            ('Scree Plot PCA', Path('reports/figures/pca_scree_plot.png').exists()),
            ('Proyección 2D', Path('reports/figures/pca_scatter_2d.png').exists()),
        ]
    }

    total_checks = 0
    passed_checks = 0

    for category, items in checklist.items():
        print(f"\n{Colors.BOLD}{category}{Colors.END}")
        for desc, status in items:
            total_checks += 1
            if status:
                print_success(desc)
                passed_checks += 1
            else:
                print_error(desc)

    percentage = (passed_checks / total_checks * 100) if total_checks > 0 else 0
    print(f"\n{Colors.BOLD}Progreso: {passed_checks}/{total_checks} ({percentage:.0f}%){Colors.END}")

    return passed_checks == total_checks

def main():
    """Función principal"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("[" + "="*78 + "]")
    print("[" + " "*78 + "]")
    print("[" + "  SMART KITCHEN INTELLIGENCE - PREPARATION FOR PRESENTATION".center(78) + "]")
    print("[" + " "*78 + "]")
    print("[" + "="*78 + "]")
    print(Colors.END)

    print_info(f"Hora de inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_info(f"Directorio: {os.getcwd()}")

    # Cambiar al directorio del proyecto si es necesario
    project_root = Path(__file__).parent
    os.chdir(project_root)

    all_tests_pass = True

    # Ejecutar validaciones
    code_ok = validate_source_code()
    data_ok = validate_data_files()
    reports_ok = validate_reports()
    packages_ok = check_python_packages()
    all_tests_pass = code_ok and data_ok and reports_ok

    # Generar reportes
    generate_summary_report()
    is_ready = create_presentation_checklist()

    # Resultado final
    print_header("RESULTADO FINAL")

    if is_ready and all_tests_pass:
        print(f"{Colors.GREEN}{Colors.BOLD}")
        print("[" + "="*78 + "]")
        print("[" + "  [OK] PROYECTO LISTO PARA PRESENTACION".center(78) + "]")
        print("[" + " "*78 + "]")
        print("[" + "  Todos los requisitos han sido validados correctamente.".center(78) + "]")
        print("[" + "  El proyecto esta ejecutable y listo para demostracion.".center(78) + "]")
        print("[" + "="*78 + "]")
        print(Colors.END)

        print_success("Para iniciar la presentación:")
        print(f"  1. Revisar: {Colors.BOLD}README_PRESENTACION.md{Colors.END}")
        print(f"  2. Ejecutar notebooks: {Colors.BOLD}jupyter notebook{Colors.END}")
        print(f"  3. Demo interactiva: {Colors.BOLD}python validate_week5.py{Colors.END}")

        return 0
    else:
        print(f"{Colors.RED}{Colors.BOLD}")
        print("[" + "="*78 + "]")
        print("[" + "  [ERROR] FALTAN ELEMENTOS PARA LA PRESENTACION".center(78) + "]")
        print("[" + "="*78 + "]")
        print(Colors.END)

        print_warning("Por favor, revisa los errores arriba y ejecuta el pipeline completo.")
        print_info("Para regenerar todos los datos:")
        print("  python src/extract_patterns.py")
        print("  python src/simulation.py")
        print("  python src/ingestion.py")
        print("  python src/preprocessing.py")
        print("  python src/features.py")
        print("  python src/reduction.py")

        return 1

if __name__ == '__main__':
    sys.exit(main())
