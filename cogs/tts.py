import discord
from discord.ext import commands
from gtts import gTTS
import os
import asyncio

class TTS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='tts')
    async def tts(self, ctx, *, text: str):
        """Transforma texto em áudio e fala na call"""
        if not ctx.author.voice:
            return await ctx.send("❌ Você precisa estar em um canal de voz!")

        vc = ctx.voice_client
        if not vc:
            try:
                vc = await ctx.author.voice.channel.connect(timeout=20, reconnect=True)
            except Exception as e:
                return await ctx.send(f"❌ Erro ao conectar na call: {e}")
        elif vc.channel != ctx.author.voice.channel:
            await vc.move_to(ctx.author.voice.channel)

        try:
            # Gerar áudio
            tts = gTTS(text=text, lang='pt')
            filename = f"tts_{ctx.guild.id}.mp3"
            tts.save(filename)

            # Verificar se o arquivo foi criado e tem conteúdo
            if not os.path.exists(filename) or os.path.getsize(filename) == 0:
                return await ctx.send("❌ Erro ao gerar o arquivo de áudio.")

            # Carregar Opus explicitamente para Linux
            if not discord.opus.is_loaded():
                try:
                    # No Replit/NixOS o Opus geralmente está disponível no PATH ou via ctypes
                    # discord.py tenta carregar automaticamente, mas vamos garantir
                    discord.opus._load_default()
                except:
                    try:
                        for opus_path in ['libopus.so.0', 'libopus.so', 'libopus-0.so.0']:
                            try:
                                discord.opus.load_opus(opus_path)
                                break
                            except:
                                continue
                    except Exception as opus_e:
                        print(f"Erro ao carregar Opus: {opus_e}")

            # Criar o áudio source simplificado
            source = discord.FFmpegPCMAudio(filename)
            
            # Garantir conexão estável
            if not vc or not vc.is_connected():
                vc = await ctx.author.voice.channel.connect(timeout=20)
            
            # Pequeno delay para o Discord processar a entrada na call e handshake
            await asyncio.sleep(2.0)

            if vc.is_playing():
                vc.stop()
            
            # Tocar com logs de debug
            def after_playing(error):
                if error:
                    print(f"Erro no playback: {error}")
                
                # Cleanup local function
                if os.path.exists(filename):
                    try:
                        os.remove(filename)
                    except:
                        pass

            vc.play(source, after=after_playing)
            await ctx.send(f"🗣️ Falando: `{text}`", delete_after=10)

        except Exception as e:
            # Garantir limpeza em caso de erro na geração/play
            if 'filename' in locals() and os.path.exists(filename):
                try: os.remove(filename)
                except: pass
            await ctx.send(f"❌ Erro no TTS: {e}")

    @commands.command(name='leave', aliases=['sair'])
    async def leave(self, ctx):
        """Faz o bot sair do canal de voz"""
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("👋 Saí do canal de voz.")
        else:
            await ctx.send("❌ Eu não estou em nenhum canal de voz.")

async def setup(bot):
    await bot.add_cog(TTS(bot))
