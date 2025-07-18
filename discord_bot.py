import discord
from discord.ext import commands, tasks
import asyncio
import logging
from typing import Optional
import os
from datetime import datetime

from config import Config
from shop_monitor import ShopMonitor
from image_recognition import ImageRecognition
from utils import format_duration, get_timestamp

class IceButterflyBot(commands.Bot):
    """Discord bot for monitoring Ice Butterfly in taming.io shop"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        
        super().__init__(command_prefix="!", intents=intents)
        
        self.logger = logging.getLogger("discord_bot")
        self.monitor = ShopMonitor(self.logger)
        self.image_recognition = ImageRecognition(
            Config.REFERENCE_IMAGE_PATH, 
            Config.MATCH_THRESHOLD, 
            self.logger
        )
        
        self.monitoring_active = False
        self.start_time = None
        self.checks_performed = 0
        self.last_status_update = None
        
        # Add commands
        self.add_commands()
    
    def add_commands(self):
        """Add bot commands"""
        
        @self.command(name="start_monitoring")
        async def start_monitoring(ctx):
            """Start monitoring the shop for Ice Butterfly"""
            if self.monitoring_active:
                await ctx.send("🤖 Monitoring is already active!")
                return
            
            await ctx.send("🚀 Starting Ice Butterfly monitoring...")
            
            # Start monitoring task
            self.monitoring_task.start()
            self.status_update_task.start()
            
            embed = discord.Embed(
                title="🦋 Ice Butterfly Monitor Started",
                description="Bot is now monitoring taming.io shop for Ice Butterfly",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="⚙️ Configuration",
                value=f"Check interval: {Config.MONITORING_INTERVAL}s\nMatch threshold: {Config.MATCH_THRESHOLD}",
                inline=False
            )
            
            await ctx.send(embed=embed)
        
        @self.command(name="stop_monitoring")
        async def stop_monitoring(ctx):
            """Stop monitoring the shop"""
            if not self.monitoring_active:
                await ctx.send("🤖 Monitoring is not active!")
                return
            
            self.monitoring_task.cancel()
            self.status_update_task.cancel()
            
            duration = format_duration(int((datetime.now() - self.start_time).total_seconds()))
            
            embed = discord.Embed(
                title="🛑 Ice Butterfly Monitor Stopped",
                description=f"Monitoring stopped after {duration}",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📊 Statistics",
                value=f"Total checks performed: {self.checks_performed}",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
            # Cleanup
            self.monitor.cleanup()
        
        @self.command(name="status")
        async def status(ctx):
            """Get current monitoring status"""
            embed = discord.Embed(
                title="📊 Ice Butterfly Monitor Status",
                color=discord.Color.green() if self.monitoring_active else discord.Color.red(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="🤖 Monitoring Status",
                value="Active" if self.monitoring_active else "Inactive",
                inline=True
            )
            
            if self.monitoring_active and self.start_time:
                duration = format_duration(int((datetime.now() - self.start_time).total_seconds()))
                embed.add_field(
                    name="⏱️ Running Duration",
                    value=duration,
                    inline=True
                )
            
            embed.add_field(
                name="🔍 Checks Performed",
                value=str(self.checks_performed),
                inline=True
            )
            
            # Shop status
            shop_status = self.monitor.get_shop_status()
            embed.add_field(
                name="🛒 Shop Status",
                value=f"Driver: {'✅' if shop_status['driver_active'] else '❌'}\n"
                      f"Logged in: {'✅' if shop_status['logged_in'] else '❌'}\n"
                      f"Shop accessible: {'✅' if shop_status['shop_accessible'] else '❌'}",
                inline=False
            )
            
            await ctx.send(embed=embed)
        
        @self.command(name="test_image")
        async def test_image(ctx):
            """Test image recognition with current screenshot"""
            if not self.monitor.driver:
                await ctx.send("❌ Monitor not active. Start monitoring first!")
                return
            
            await ctx.send("📸 Taking test screenshot...")
            
            screenshot_path = self.monitor.take_screenshot()
            if not screenshot_path:
                await ctx.send("❌ Failed to take screenshot!")
                return
            
            # Perform image recognition
            found, confidence, position = self.image_recognition.detect_ice_butterfly(screenshot_path)
            
            embed = discord.Embed(
                title="🔍 Image Recognition Test",
                color=discord.Color.green() if found else discord.Color.orange(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="🎯 Detection Result",
                value="Ice Butterfly Found!" if found else "Ice Butterfly Not Found",
                inline=True
            )
            
            embed.add_field(
                name="📊 Confidence",
                value=f"{confidence:.3f}",
                inline=True
            )
            
            embed.add_field(
                name="🎯 Threshold",
                value=f"{Config.MATCH_THRESHOLD}",
                inline=True
            )
            
            if position:
                embed.add_field(
                    name="📍 Position",
                    value=f"({position[0]}, {position[1]})",
                    inline=True
                )
            
            await ctx.send(embed=embed)
            
            # Send screenshot if small enough
            if os.path.exists(screenshot_path) and os.path.getsize(screenshot_path) < 8000000:  # 8MB limit
                try:
                    await ctx.send(file=discord.File(screenshot_path))
                except Exception as e:
                    self.logger.error(f"Failed to send screenshot: {str(e)}")
        
        @self.command(name="restart")
        async def restart(ctx):
            """Restart the browser session"""
            await ctx.send("🔄 Restarting browser session...")
            
            success = self.monitor.restart_session()
            
            if success:
                embed = discord.Embed(
                    title="✅ Browser Session Restarted",
                    description="Successfully restarted browser and logged in",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
            else:
                embed = discord.Embed(
                    title="❌ Browser Restart Failed",
                    description="Failed to restart browser session",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
            
            await ctx.send(embed=embed)
    
    async def on_ready(self):
        """Called when bot is ready"""
        self.logger.info(f"Bot logged in as {self.user}")
        
        # Send startup message
        for guild in self.guilds:
            channel = discord.utils.get(guild.channels, name=Config.DISCORD_CHANNEL_NAME)
            if channel and hasattr(channel, 'send'):
                embed = discord.Embed(
                    title="🤖 Ice Butterfly Monitor Online",
                    description="Bot is ready to monitor taming.io shop!",
                    color=discord.Color.blue(),
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="🚀 Getting Started",
                    value="Use `!start_monitoring` to begin monitoring",
                    inline=False
                )
                
                await channel.send(embed=embed)
                break
    
    @tasks.loop(seconds=Config.MONITORING_INTERVAL)
    async def monitoring_task(self):
        """Main monitoring task"""
        try:
            if not self.monitoring_active:
                self.monitoring_active = True
                self.start_time = datetime.now()
                self.logger.info("Monitoring task started")
                
                # Initialize browser session
                if not self.monitor.setup_driver():
                    await self.send_error_message("Failed to setup browser driver")
                    return
                
                if not self.monitor.navigate_to_game():
                    await self.send_error_message("Failed to navigate to taming.io")
                    return
                
                if not self.monitor.login_as_guest():
                    await self.send_error_message("Failed to login as guest")
                    return
                
                if not self.monitor.access_shop():
                    await self.send_error_message("Failed to access shop")
                    return
                
                await self.send_success_message("✅ Successfully connected to taming.io shop!")
            
            # Monitor for Ice Butterfly using enhanced method
            is_found = self.monitor.monitor_for_ice_butterfly()
            
            self.checks_performed += 1
            
            if is_found:
                # Get screenshot and perform detailed analysis for confidence metrics
                screenshot_path = self.monitor.last_screenshot_path
                if screenshot_path:
                    found, confidence, position = self.image_recognition.detect_ice_butterfly(screenshot_path)
                    await self.send_butterfly_found_message(confidence, position, screenshot_path)
                    self.monitoring_task.stop()
                    self.monitoring_active = False
                    self.logger.info("🦋 Ice Butterfly found! Monitoring stopped.")
                else:
                    await self.send_butterfly_found_message(0.9, (0, 0), None)
            else:
                self.logger.debug(f"Check #{self.checks_performed}: Ice Butterfly not found in potion store")
        
        except Exception as e:
            self.logger.error(f"Error in monitoring task: {str(e)}")
            await self.send_error_message(f"Monitoring error: {str(e)}")
    
    @tasks.loop(seconds=Config.STATUS_UPDATE_INTERVAL)
    async def status_update_task(self):
        """Send periodic status updates"""
        try:
            if not self.monitoring_active:
                return
            
            duration = format_duration(int((datetime.now() - self.start_time).total_seconds()))
            
            embed = discord.Embed(
                title="📊 Monitoring Status Update",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="⏱️ Running Duration",
                value=duration,
                inline=True
            )
            
            embed.add_field(
                name="🔍 Checks Performed",
                value=str(self.checks_performed),
                inline=True
            )
            
            embed.add_field(
                name="🤖 Status",
                value="Monitoring Active",
                inline=True
            )
            
            await self.send_embed(embed)
            
        except Exception as e:
            self.logger.error(f"Error in status update task: {str(e)}")
    
    async def send_butterfly_found_message(self, confidence: float, position: tuple, screenshot_path: str):
        """Send Ice Butterfly found notification"""
        embed = discord.Embed(
            title="🦋 ICE BUTTERFLY FOUND! 🦋",
            description="The Ice Butterfly has been detected in the shop!",
            color=discord.Color.gold(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="🎯 Confidence",
            value=f"{confidence:.3f}",
            inline=True
        )
        
        embed.add_field(
            name="📍 Position",
            value=f"({position[0]}, {position[1]})",
            inline=True
        )
        
        embed.add_field(
            name="⏰ Time",
            value=get_timestamp(),
            inline=True
        )
        
        embed.add_field(
            name="🚀 Action Required",
            value="Go to taming.io shop immediately!",
            inline=False
        )
        
        await self.send_embed(embed)
        
        # Send screenshot if available
        if os.path.exists(screenshot_path) and os.path.getsize(screenshot_path) < 8000000:
            try:
                for guild in self.guilds:
                    channel = discord.utils.get(guild.channels, name=Config.DISCORD_CHANNEL_NAME)
                    if channel and hasattr(channel, 'send'):
                        await channel.send(file=discord.File(screenshot_path))
                        break
            except Exception as e:
                self.logger.error(f"Failed to send screenshot: {str(e)}")
    
    async def send_success_message(self, message: str):
        """Send success message to Discord"""
        embed = discord.Embed(
            title="✅ Success",
            description=message,
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        
        await self.send_embed(embed)
    
    async def send_error_message(self, message: str):
        """Send error message to Discord"""
        embed = discord.Embed(
            title="❌ Error",
            description=message,
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        
        await self.send_embed(embed)
    
    async def send_embed(self, embed: discord.Embed):
        """Send embed to Discord channel"""
        for guild in self.guilds:
            channel = discord.utils.get(guild.channels, name=Config.DISCORD_CHANNEL_NAME)
            if channel and hasattr(channel, 'send'):
                await channel.send(embed=embed)
                break
