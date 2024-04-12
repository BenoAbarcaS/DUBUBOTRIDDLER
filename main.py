# main.py
import discord
from discord.ext import commands
from discord import FFmpegPCMAudio
import asyncio
import random
import sqlite3
from acertijos import acertijos
from config import TOKEN

intents = discord.Intents.all()
intents.members = True
client = commands.Bot(command_prefix='!', intents=intents)

conn = sqlite3.connect('acertijos.db')
c = conn.cursor()

c.execute('''
          CREATE TABLE IF NOT EXISTS usuarios (
              usuario_id INTEGER PRIMARY KEY,
              puntos INTEGER DEFAULT 0,
              habitacion_actual INTEGER DEFAULT 0
          )
          ''')

c.execute('''
          CREATE TABLE IF NOT EXISTS acertijos (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              descripcion TEXT,
              respuesta TEXT,
              imagen_url TEXT
          )
          ''')

# Agregar algunos acertijos de ejemplo con respuestas e imágenes
for acertijo in acertijos:
    c.execute("INSERT OR IGNORE INTO acertijos (descripcion, respuesta, imagen_url) VALUES (?, ?, ?)",
              (acertijo['descripcion'], acertijo['respuesta'], acertijo['imagen_url']))

@client.event
async def on_ready():
    print(f'Logeado como {client.user}')

@client.command(pass_context=True)
async def acertijo(ctx):
    usuario_id = ctx.author.id

    c.execute("SELECT * FROM usuarios WHERE usuario_id=?", (usuario_id,))
    usuario_data = c.fetchone()

    if usuario_data:
        habitacion_actual = usuario_data[2]
    else:
        habitacion_actual = 1
        c.execute("INSERT OR IGNORE INTO usuarios (usuario_id, habitacion_actual) VALUES (?, ?)", (usuario_id, habitacion_actual))
        conn.commit()

    c.execute("SELECT * FROM acertijos WHERE id=?", (habitacion_actual,))
    acertijo_data = c.fetchone()

    if not acertijo_data:
        await ctx.send("Has completado todas las habitaciones. ¡Felicidades!")
        return

    acertijo_id, descripcion_acertijo, respuesta_acertijo, imagen_url_acertijo = acertijo_data

    embed = discord.Embed(title=f"Habitación {habitacion_actual} - Acertijo", description=f"**{descripcion_acertijo}**", color=discord.Color.blue())

    if imagen_url_acertijo:
        embed.set_image(url=imagen_url_acertijo)

    await ctx.send(embed=embed)

    try:
        respuesta_usuario = await client.wait_for("message", timeout=30, check=lambda m: m.author == ctx.author)
    except asyncio.TimeoutError:
        await ctx.send("Se agotó el tiempo. ¡Desafío fallido!")
        return

    if respuesta_usuario.content.lower() == respuesta_acertijo:
        puntos_ganados = 10
        c.execute("UPDATE usuarios SET puntos = puntos + ?, habitacion_actual = habitacion_actual + 1 WHERE usuario_id = ?", (puntos_ganados, usuario_id))
        conn.commit()

        embed_respuesta = discord.Embed(description=f"¡Correcto! Has resuelto el acertijo. ¡Ganaste {puntos_ganados} puntos! ¿Quieres ir a la siguiente habitación? Responde con 'si' para continuar o 'no' para continuar más tarde.", color=discord.Color.green())
        await ctx.send(embed=embed_respuesta)

        try:
            respuesta_siguiente_habitacion = await client.wait_for("message", timeout=30, check=lambda m: m.author == ctx.author)
            if respuesta_siguiente_habitacion.content.lower() == 'si':
                await acertijo(ctx)
            elif respuesta_siguiente_habitacion.content.lower() == 'no':
                embed_continuar = discord.Embed(description="Puedes continuar en cualquier momento. ¡Buena suerte!", color=discord.Color.blue())
                await ctx.send(embed=embed_continuar)
            else:
                embed_respuesta_invalida = discord.Embed(description="Respuesta no válida. Puedes continuar en cualquier momento. ¡Buena suerte!", color=discord.Color.red())
                await ctx.send(embed=embed_respuesta_invalida)
        except asyncio.TimeoutError:
            embed_tiempo_agotado = discord.Embed(description="Se agotó el tiempo. Te has quedado en la habitación actual.", color=discord.Color.red())
            await ctx.send(embed=embed_tiempo_agotado)
    else:
        embed_incorrecto = discord.Embed(description="Incorrecto. ¡Desafío fallido!", color=discord.Color.red())
        await ctx.send(embed=embed_incorrecto)

@client.command(pass_context=True)
async def top(ctx):
    c.execute("SELECT usuario_id, habitacion_actual, puntos FROM usuarios ORDER BY habitacion_actual DESC, puntos DESC LIMIT 10")
    top_usuarios = c.fetchall()

    if top_usuarios:
        mensaje_top = f"Top 10 Usuarios:\n"
        for i, (usuario_id, habitacion_actual, puntos) in enumerate(top_usuarios, start=1):
            usuario = await client.fetch_user(usuario_id)

            # Crear el Embed sin URL de la miniatura
            embed = discord.Embed(description=f"{i}. {usuario.name} - Habitación {habitacion_actual} - Puntos: {puntos}", color=discord.Color.gold())

            mensaje_top += f"{i}. {usuario.name} - Habitación {habitacion_actual} - Puntos: {puntos}\n"
            await ctx.send(embed=embed)
    else:
        await ctx.send("Aún no hay usuarios en el top. ¡Anímate y resuelve algunos acertijos!")




client.run(TOKEN)