"""
Script de prueba para la API
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Prueba el endpoint de health check"""
    print("1. Probando /health...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_model_info():
    """Prueba el endpoint de información del modelo"""
    print("\n2. Probando /model/info...")
    try:
        response = requests.get(f"{BASE_URL}/model/info")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"   Error: {e}")
        return False

def test_predict_point():
    """Prueba la predicción de un solo punto"""
    print("\n3. Probando /predict/point...")
    data = {
        "latitud": 6.2442,
        "longitud": -75.5812
    }
    try:
        response = requests.post(
            f"{BASE_URL}/predict/point",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Probabilidad: {result['probabilidad']:.4f}")
            print(f"   Riesgo: {result['riesgo']}")
        else:
            print(f"   Error: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"   Error: {e}")
        return False

def test_predict_route():
    """Prueba la predicción de una ruta"""
    print("\n4. Probando /predict/route...")
    data = {
        "puntos": [
            {"latitud": 6.2442, "longitud": -75.5812},
            {"latitud": 6.2500, "longitud": -75.5800},
            {"latitud": 6.2550, "longitud": -75.5750}
        ]
    }
    try:
        response = requests.post(
            f"{BASE_URL}/predict/route",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Puntos analizados: {len(result['puntos'])}")
            print(f"   Probabilidad promedio: {result['probabilidad_promedio']:.4f}")
            print(f"   Riesgo alto: {result['riesgo_alto_count']}")
            print(f"   Riesgo medio: {result['riesgo_medio_count']}")
            print(f"   Riesgo bajo: {result['riesgo_bajo_count']}")
        else:
            print(f"   Error: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"   Error: {e}")
        return False

def main():
    """Ejecuta todas las pruebas"""
    print("=" * 60)
    print("PRUEBAS DE LA API")
    print("=" * 60)
    
    results = []
    results.append(("Health Check", test_health()))
    results.append(("Model Info", test_model_info()))
    results.append(("Predict Point", test_predict_point()))
    results.append(("Predict Route", test_predict_route()))
    
    print("\n" + "=" * 60)
    print("RESUMEN DE PRUEBAS")
    print("=" * 60)
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    print(f"\n{'✅ Todas las pruebas pasaron' if all_passed else '❌ Algunas pruebas fallaron'}")

if __name__ == "__main__":
    main()

