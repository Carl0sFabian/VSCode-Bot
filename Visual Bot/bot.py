import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import requests
import json

# --- 1. Configuración Inicial ---

load_dotenv()
TOKEN = os.getenv('TOKEN')
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# --- 2. Configuración de la API de VS Code ---

MARKETPLACE_API_URL = "https://marketplace.visualstudio.com/_apis/public/gallery/extensionquery"

API_HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json;api-version=7.1-preview.1',
}

def build_api_payload(search_term, count=3): # Mantenemos 3 resultados
    """
    Construye el 'body' (payload) que la API de VS Code espera.
    """
    return {
        "filters": [
            {
                "criteria": [
                    {"filterType": 10, "value": search_term}, # 10 = Búsqueda por texto
                    {"filterType": 12, "value": "Microsoft.VisualStudio.Code"}
                ],
                "pageSize": count,
                "pageNumber": 1,
                "sortBy": 4,
                "sortOrder": 0
            }
        ],
        "flags": 914
    }

# --- 3. Evento "Ready" (Actualizado para la insignia) ---

@bot.event
async def on_ready():
    # --- ¡NUEVO! --- Sincroniza los comandos slash (como /ping)
    await bot.tree.sync() 
    print(f'¡Bot conectado como {bot.user}!')
    print('----------------------------------')

# --- 4. Comando Slash (/) para la Insignia ---

@bot.tree.command(name="ping", description="Comando de prueba para la insignia de programador.")
async def ping(interaction: discord.Interaction):
    """Responde 'Pong' a un comando /ping."""
    await interaction.response.send_message(f"¡Pong! 🏓 Soy un bot activo.")

# --- 5. Comando Principal "!ext" ---

@bot.command(name='ext')
async def search_extensions(ctx, *, search_query: str):
    """
    Busca extensiones y envía un mensaje individual 
    para cada una, con su propio logo.
    """
    
    if not search_query:
        await ctx.send("⚠️ ¡Debes escribir qué buscar! \nPor ejemplo: `!ext python`")
        return

    print(f"Iniciando búsqueda en la API para: '{search_query}'")

    async with ctx.typing():
        try:
            payload = build_api_payload(search_query) # Pedirá 3 resultados
            response = requests.post(
                MARKETPLACE_API_URL, 
                json=payload,
                headers=API_HEADERS
            )
            response.raise_for_status() 
            data = response.json()
            extensions = data.get('results', [{}])[0].get('extensions', [])
            
            if not extensions:
                await ctx.send(f"😥 No encontré extensiones para la búsqueda: `{search_query}`")
                return

            print(f"Búsqueda exitosa. Enviando {len(extensions)} embeds individuales...")
            
            await ctx.send(f"--- 🔎 Resultados para: \"{search_query}\" ---")

            for ext in extensions:
                # 1. Obtener datos de la extensión
                display_name = ext.get('displayName', 'N/A')
                publisher = ext.get('publisher', {}).get('displayName', 'N/A')
                unique_id = f"{ext.get('publisher', {}).get('publisherName', '')}.{ext.get('extensionName', '')}"
                marketplace_url = f"https://marketplace.visualstudio.com/items?itemName={unique_id}"
                
                # 2. Obtener el logo de ESTA extensión (Ruta corregida)
                ext_files = ext.get('versions', [{}])[0].get('files', [])
                
                icon_url = None
                for file in ext_files:
                    if file.get('assetType') == 'Microsoft.VisualStudio.Services.Icons.Small':
                        icon_url = file.get('source')
                        break
                if not icon_url: # Si no hay icono "Small", busca el "Default"
                    for file in ext_files:
                         if file.get('assetType') == 'Microsoft.VisualStudio.Services.Icons.Default':
                            icon_url = file.get('source')
                            break
                
                # 3. Crear un Embed NUEVO solo para esta extensión
                embed = discord.Embed(
                    title=f"{display_name}",
                    description=f"**Publicado por:** {publisher}\n"
                                f"**[Ver en Marketplace]({marketplace_url})**",
                    color=discord.Color.blue()
                )
                
                # 4. Poner su logo como thumbnail
                if icon_url:
                    embed.set_thumbnail(url=icon_url)
                
                # 5. Enviar este Embed
                await ctx.send(embed=embed)
            
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error: {http_err}") 
            print(f"Respuesta de la API (Error): {http_err.response.text}")
            await ctx.send(f"Error al contactar la API de VS Code. (Error: {http_err.response.status_code})")
        
        except Exception as err:
            print(f"Error inesperado: {err}")
            await ctx.send(f"Ocurrió un error inesperado al procesar tu solicitud.")

# --- 6. Ejecutar el Bot ---
if TOKEN:
    bot.run(TOKEN)
else:
    print("Error: No se encontró el TOKEN. Asegúrate de crear un archivo .env")