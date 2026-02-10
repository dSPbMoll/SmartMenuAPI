import httpx
import random
import asyncio

async def llamar_receta_aleatoria():
    # 1. Definimos la base de la URL (donde vive tu API)
    BASE_URL = "http://localhost:8000/userApi/v1"
    
    # 2. Generamos un ID aleatorio (por ejemplo del 1 al 50)
    recipe_id = random.randint(1, 50)
    
    # 3. Construimos el endpoint completo
    endpoint = f"{BASE_URL}/genericRecipe/{recipe_id}"
    
    print(f"🚀 Llamando al endpoint: {endpoint}...")

    # 4. Hacemos la petición real
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(endpoint)
            
            # 5. Manejamos la respuesta según los códigos que definiste
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Receta encontrada: {data['name']}")
                print(f"👨‍🍳 Consejo del chef: {data['cheffAdvice']}")
            elif response.status_code == 404:
                print("❌ Error: La receta no existe en la BD.")
            else:
                print(f"⚠️ El servidor respondió con código: {response.status_code}")
                
        except httpx.ConnectError:
            print("🔥 Error: ¿Encendiste el servidor? No se pudo conectar.")

# Ejecutar la función
if __name__ == "__main__":
    asyncio.run(llamar_receta_aleatoria())