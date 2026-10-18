"""Comprehensive application diagnostic and fix verification"""
import sys
import os
import traceback
from datetime import date

# Set working directory
os.chdir(r"C:\Users\A SASIKINTH\OneDrive\Desktop\ai_career\AI_carrer_guide")
sys.path.insert(0, ".")

def test_imports():
    print("\n=== Testing Imports ===")
    try:
        import fastapi
        import falkordb
        import langgraph
        import streamlit
        import google.genai
        print("✓ All critical packages imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_graph_initialization():
    print("\n=== Testing Graph Initialization ===")
    try:
        from backend.config.db import get_graph
        from backend.database.setup import bootstrap_graph
        
        graph = get_graph()
        print(f"✓ Graph created: {type(graph).__name__}")
        
        # Test the methods exist
        assert hasattr(graph, 'list_indices'), "Missing list_indices method"
        assert hasattr(graph, 'create_node_range_index'), "Missing create_node_range_index method"
        assert hasattr(graph, 'query'), "Missing query method"
        print("✓ Required graph methods exist")
        
        # Test bootstrap
        counts = bootstrap_graph(graph)
        print(f"✓ Bootstrap successful: {counts}")
        return True
    except Exception as e:
        print(f"✗ Graph initialization failed: {e}")
        traceback.print_exc()
        return False

def test_student_profile():
    print("\n=== Testing Student Profile Retrieval ===")
    try:
        from backend.config.db import get_graph
        from backend.database.read_ops import get_student_profile
        
        graph = get_graph()
        profile = get_student_profile(graph, "seed-student-001")
        
        if profile:
            print(f"✓ Retrieved profile: {profile['name']}")
            print(f"  - Skills: {len(profile.get('skills', []))}")
            print(f"  - Goals: {len(profile.get('goals', []))}")
            print(f"  - Projects: {len(profile.get('projects', []))}")
            return True
        else:
            print("✗ Profile not found for seed-student-001")
            return False
    except Exception as e:
        print(f"✗ Profile retrieval failed: {e}")
        traceback.print_exc()
        return False

def test_opportunities():
    print("\n=== Testing Opportunities Retrieval ===")
    try:
        from backend.config.db import get_graph
        from backend.database.read_ops import list_opportunities
        
        graph = get_graph()
        opps = list_opportunities(
            graph,
            student_id="seed-student-001",
            limit=5,
            include_demo=True
        )
        print(f"✓ Retrieved {len(opps)} opportunities")
        if opps:
            print(f"  Sample: {opps[0]['title']}")
        return True
    except Exception as e:
        print(f"✗ Opportunities retrieval failed: {e}")
        traceback.print_exc()
        return False

def test_fastapi_app():
    print("\n=== Testing FastAPI Application ===")
    try:
        from backend.main import app
        print(f"✓ FastAPI app created: {app.title}")
        print(f"  Routes: {len(app.routes)}")
        return True
    except Exception as e:
        print(f"✗ FastAPI app creation failed: {e}")
        traceback.print_exc()
        return False

def main():
    print("="*60)
    print(" AI Career Mentor - Comprehensive Diagnostic")
    print("="*60)
    
    results = []
    results.append(("Imports", test_imports()))
    results.append(("Graph Init", test_graph_initialization()))
    results.append(("Student Profile", test_student_profile()))
    results.append(("Opportunities", test_opportunities()))
    results.append(("FastAPI App", test_fastapi_app()))
    
    print("\n" + "="*60)
    print(" SUMMARY")
    print("="*60)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - Application is ready!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed - see details above")
        return 1

if __name__ == "__main__":
    sys.exit(main())