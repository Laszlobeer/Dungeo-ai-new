#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import sys
import urllib.request
import urllib.error
import urllib.parse
import subprocess
import textwrap
import os
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import time
from pathlib import Path
# Rich imports for UI
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.table import Table
from rich.markdown import Markdown
from rich.live import Live
from rich.spinner import Spinner
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.layout import Layout
from rich.text import Text
from rich.syntax import Syntax
from rich.columns import Columns
import threading

# Initialize Rich console
console = Console()

CONFIG = {
    "OLLAMA_URL": "http://127.0.0.1:11434",
    "ALLTALK_TTS_URL": "http://127.0.0.1:7851",  # Default AllTalk TTS URL
    "REQUEST_TIMEOUT": 120,
    "MAX_HISTORY_TOKENS": 3500,
    "MAX_HISTORY_TURNS": 10,
    "SAVE_DIR": "adventure_saves",
    "EXPORT_DIR": "adventure_exports",
}

STOP_TOKENS = ["\n", "Player:", "Dungeon Master:", "System:", "\n---"]

ROLE_STARTERS = {
    "Fantasy": {
        "Peasant": "You're working in the fields of a small village when",
        "Noble": "You're waking up from your bed in your mansion when",
        "Mage": "You're studying ancient tomes in your tower when",
        "Knight": "You're training in the castle courtyard when",
        "Ranger": "You're tracking animals in the deep forest when",
        "Thief": "You're casing a noble's house from an alley in a city when",
        "Bard": "You're performing in a crowded tavern when",
        "Cleric": "You're tending to the sick in the temple when",
        "Assassin": "You're preparing to attack your target in the shadows when",
        "Paladin": "You're praying at the altar of your deity when",
        "Alchemist": "You're carefully measuring reagents in your alchemy lab when",
        "Druid": "You're communing with nature in the sacred grove when",
        "Warlock": "You're negotiating with your otherworldly patron when",
        "Monk": "You're meditating in the monastery courtyard when",
        "Sorcerer": "You're struggling to control your innate magical powers when",
        "Beastmaster": "You're training your animal companions in the forest clearing when",
        "Enchanter": "You're imbuing magical properties into a mundane object when",
        "Blacksmith": "You're forging a new weapon at your anvil when",
        "Merchant": "You're haggling with customers at the marketplace when",
        "Gladiator": "You're preparing for combat in the arena when",
        "Wizard": "You're researching new spells in your arcane library when"
    },
    "Sci-Fi": {
        "Space Marine": "You're conducting patrol on a derelict space station when",
        "Scientist": "You're analyzing alien samples in your lab when",
        "Android": "You're performing system diagnostics on your ship when",
        "Pilot": "You're navigating through an asteroid field when",
        "Engineer": "You're repairing the FTL drive when",
        "Alien Diplomat": "You're negotiating with an alien delegation when",
        "Bounty Hunter": "You're tracking a target through a spaceport when",
        "Starship Captain": "You're commanding the bridge during warp travel when",
        "Space Pirate": "You're plotting your next raid from your starship's bridge when",
        "Navigator": "You're charting a course through uncharted space when",
        "Robot Technician": "You're repairing a malfunctioning android when",
        "Cybernetic Soldier": "You're calibrating your combat implants when",
        "Explorer": "You're scanning a newly discovered planet when",
        "Astrobiologist": "You're studying alien life forms in your lab when",
        "Quantum Hacker": "You're breaching a corporate firewall when",
        "Galactic Trader": "You're negotiating a deal for rare resources when",
        "AI Specialist": "You're debugging a sentient AI's personality matrix when",
        "Terraformer": "You're monitoring atmospheric changes on a new colony world when",
        "Cyberneticist": "You're installing neural enhancements in a patient when"
    },
    "Cyberpunk": {
        "Hacker": "You're infiltrating a corporate network when",
        "Street Samurai": "You're patrolling the neon-lit streets when",
        "Corporate Agent": "You're closing a deal in a high-rise office when",
        "Techie": "You're modifying cyberware in your workshop when",
        "Rebel Leader": "You're planning a raid on a corporate facility when",
        "Cyborg": "You're calibrating your cybernetic enhancements when",
        "Drone Operator": "You're controlling surveillance drones from your command center when",
        "Synth Dealer": "You're negotiating a deal for illegal cybernetics when",
        "Information Courier": "You're delivering sensitive data through dangerous streets when",
        "Augmentation Engineer": "You're installing cyberware in a back-alley clinic when",
        "Black Market Dealer": "You're arranging contraband in your hidden shop when",
        "Scumbag": "You're looking for an easy mark in the slums when",
        "Police": "You're patrolling the neon-drenched streets when"
    },
    "Post-Apocalyptic": {
        "Survivor": "You're scavenging in the ruins of an old city when",
        "Scavenger": "You're searching a pre-collapse bunker when",
        "Raider": "You're ambushing a convoy in the wasteland when",
        "Medic": "You're treating radiation sickness in your clinic when",
        "Cult Leader": "You're preaching to your followers at a ritual when",
        "Mutant": "You're hiding your mutations in a settlement when",
        "Trader": "You're bartering supplies at a wasteland outpost when",
        "Berserker": "You're sharpening your weapons for the next raid when",
        "Soldier": "You're guarding a settlement from raiders when"
    },
    "1880": {
        "Thief": "You're lurking in the shadows of the city alleyways when",
        "Beggar": "You're sitting on the cold street corner with your cup when",
        "Detective": "You're examining a clue at the crime scene when",
        "Rich Man": "You're enjoying a cigar in your luxurious study when",
        "Factory Worker": "You're toiling away in the noisy factory when",
        "Child": "You're playing with a hoop in the street when",
        "Orphan": "You're searching for scraps in the trash bins when",
        "Murderer": "You're cleaning blood from your hands in a dark alley when",
        "Butcher": "You're sharpening your knives behind the counter when",
        "Baker": "You're kneading dough in the early morning hours when",
        "Banker": "You're counting stacks of money in your office when",
        "Policeman": "You're walking your beat on the foggy streets when"
    },
    "WW1": {
        "Soldier (French)": "You're huddled in the muddy trenches of the Western Front when",
        "Soldier (English)": "You're writing a letter home by candlelight when",
        "Soldier (Russian)": "You're shivering in the frozen Eastern Front when",
        "Soldier (Italian)": "You're climbing the steep Alpine slopes when",
        "Soldier (USA)": "You're arriving fresh to the European theater when",
        "Soldier (Japanese)": "You're guarding a Pacific outpost when",
        "Soldier (German)": "You're preparing for a night raid when",
        "Soldier (Austrian)": "You're defending the crumbling empire's borders when",
        "Soldier (Bulgarian)": "You're holding the line in the Balkans when",
        "Civilian": "You're queuing for rationed bread when",
        "Resistance Fighter": "You're transmitting coded messages in an attic when"
    },
    "WW2": {
        "Soldier (American)": "You're storming the beaches of Normandy under heavy German fire when",
        "Soldier (British)": "You're preparing for the D-Day invasion aboard a troop ship when",
        "Soldier (Russian)": "You're defending Stalingrad house by house against the German advance when",
        "Soldier (German)": "You're manning a machine gun nest on the Atlantic Wall when",
        "Soldier (Italian)": "You're retreating through the Italian countryside after the Allied invasion when",
        "Soldier (French)": "You're joining the French Resistance after the fall of Paris when",
        "Soldier (Japanese)": "You're defending a Pacific island against American marines when",
        "Soldier (Canadian)": "You're fighting through the rubble of a French town during the liberation when",
        "Soldier (Australian)": "You're battling Japanese forces in the jungles of New Guinea when",
        "Resistance Fighter": "You're sabotaging German supply lines under cover of darkness when",
        "Spy": "You're transmitting coded messages from occupied territory when",
        "Pilot (RAF)": "You're scrambling to intercept German bombers during the Battle of Britain when",
        "Pilot (Luftwaffe)": "You're flying a bombing mission over England when",
        "Tank Commander": "You're leading a Sherman tank through the Ardennes forest when",
        "Sniper": "You're concealed in a ruined building, watching for enemy movement when",
        "Medic": "You're treating wounded soldiers under fire on the front lines when",
        "Naval Officer": "You're commanding a destroyer in the North Atlantic convoy when",
        "Paratrooper": "You're jumping into enemy territory behind German lines when",
        "Commando": "You're conducting a covert raid on a German occupied facility when"
    },
    "1925 New York": {
        "Mafia Boss": "You're counting your illicit earnings in a backroom speakeasy when",
        "Drunk": "You're stumbling out of a jazz club at dawn when",
        "Police Officer": "You're taking bribes from a known bootlegger when",
        "Detective": "You're examining a gangland murder scene when",
        "Factory Worker": "You're assembling Model Ts on the production line when",
        "Bootlegger": "You're transporting a shipment of illegal hooch when"
    },
    "Roman Empire": {
        "Slave": "You're carrying heavy stones under the hot sun when",
        "Gladiator": "You're sharpening your sword before entering the arena when",
        "Beggar": "You're pleading for coins near the Forum when",
        "Senator": "You're plotting political maneuvers in the Curia when",
        "Imperator": "You're reviewing legions from your palace balcony when",
        "Soldier": "You're marching on the frontier when",
        "Noble": "You're hosting a decadent feast in your villa when",
        "Trader": "You're haggling over spices in the market when",
        "Peasant": "You're tending your meager crops when",
        "Priest": "You're sacrificing a goat at the temple when",
        "Barbarian": "You're sharpening your axe beyond the limes when",
        "Philosopher": "You're contemplating the nature of existence when",
        "Mathematician": "You're calculating the circumference of the Earth when",
        "Semi-God": "You're channeling divine powers on Mount Olympus when"
    },
    "French Revolution": {
        "Peasant": "You're marching toward the Bastille with a pitchfork when",
        "King": "You're dining lavishly while Paris starves when",
        "Noble": "You're hiding your family jewels from revolutionaries when",
        "Beggar": "You're rummaging through aristocratic trash bins when",
        "Soldier": "You're guarding the Tuileries Palace when",
        "General": "You're planning troop deployments against rebels when",
        "Resistance": "You're printing revolutionary pamphlets in secret when",
        "Politician": "You're giving a fiery speech at the National Assembly when"
    }
}

GENRE_DESCRIPTIONS = {
    "Fantasy": "You are in a world of magic and medieval fantasy, where dragons soar through skies and ancient ruins hold forgotten treasures. The air is thick with possibility, and every shadow could hide friend or foe.",
    "Sci-Fi": "You are in the distant future, with advanced technology that blurs the line between human and machine. Starships traverse wormholes, alien civilizations await discovery, and artificial intelligences ponder their existence.",
    "Cyberpunk": "You are in a dystopian future dominated by megacorporations, where neon lights reflect off rain-slicked streets and cybernetic enhancements are as common as clothing. The line between human and machine has blurred beyond recognition.",
    "Post-Apocalyptic": "You are in a world after a catastrophic event, where survival is the only law. Ruined cities stand as monuments to the past, while scavengers pick through the remains of civilization.",
    "1880": "You are in the late 19th century during the Industrial Revolution, where steam engines power progress and soot fills the air. The world is changing rapidly, and not everyone is keeping up.",
    "WW1": "You are in the trenches and battlefields of World War I, where modern warfare meets outdated tactics. The ground trembles with artillery, and gas masks are as essential as rifles.",
    "WW2": "You are in the global conflict of World War II, where the fate of nations hangs in the balance. From the beaches of Normandy to the Pacific islands, courage and sacrifice define this era.",
    "1925 New York": "You are in the Roaring Twenties in New York City, where jazz fills smoky speakeasies and fortunes are made overnight. Prohibition has created a shadow economy run by charismatic gangsters.",
    "Roman Empire": "You are in ancient Rome at the height of its power, where emperors command legions and senators plot in marble halls. The city is a tapestry of decadence and ambition.",
    "French Revolution": "You are in France during the revolution, where the streets run red with the blood of aristocrats and the air smells of smoke and rebellion. Liberty, equality, and fraternity are the new gods."
}

DM_SYSTEM_PROMPT = """
You are a responsive Dungeon Master who narrates IMMEDIATE CONSEQUENCES based on the player's EXACT action.
STRICT RULES:
1. ACTION-RESPONSE CHAIN: Your response MUST be a direct, logical consequence of the player's SPECIFIC action.
2. SHORT & FOCUSED: 2-4 sentences maximum. Every sentence must relate to the player's action.
3. NO SETUP: Don't describe what led to the action. The player already knows.
4. NO QUESTIONS: Never ask "what do you do next?" or similar.
5. NO NEW UNRELATED EVENTS: Only describe things directly resulting from the player's action.
6. PHYSICAL LAWS: Respect physics, magic systems, and genre rules.
7. CAUSE & EFFECT: Show clear cause-effect relationships.
8. IMMEDIATE TIMEFRAME: Describe what happens RIGHT AFTER the action.
9. NO PASSIVE VOICE: Use active voice to emphasize player agency ("The door splinters" not "The door is splintered").
10. CONSEQUENCE-FIRST: Start with the direct result of the action before describing reactions.

RESPONSE TEMPLATE:
1. Direct physical result of the action (e.g., "Your sword strikes the orc's shoulder")
2. Immediate environmental reaction (e.g., "Blood sprays across the stone floor")
3. Character/NPC reaction (e.g., "The orc roars in pain and staggers back")
4. New tactical situation (e.g., "Its guard is broken, leaving its chest exposed")

BAD EXAMPLE (Vague/Passive):
"You try to open the door. Something happens in the distance."

GOOD EXAMPLE (Specific/Active):
"Your shoulder slams into the wooden door with a loud crack. The door splinters but holds, rattling in its frame. From inside, you hear frantic shuffling and a muffled curse. The door is now visibly weakened but still barred."

Always analyze the player's action word-by-word and respond accordingly with immediate, logical consequences.
"""

ACTION_ANALYSIS_PROMPT = """
ANALYZE THE PLAYER'S ACTION CAREFULLY:
- What exactly did they say they're doing? (verbs, objects, targets)
- What would realistically happen IMMEDIATELY after this action?
- How does the world/react to this SPECIFIC action? (not generic reactions)
- What are the direct physical/logical consequences?
- Does this action succeed, fail, or partially succeed based on context?

RESPOND ONLY with narrative consequences. No commentary, no questions, no setup.
"""

@dataclass
class GameState:
    """Game state management"""
    model: str
    player_name: str
    genre: str
    role: str
    history: List[Dict[str, str]]
    use_tts: bool = False
    tts_voice: Optional[str] = None
    start_time: Optional[datetime] = None
    
    def __post_init__(self):
        if self.start_time is None:
            self.start_time = datetime.now()
    
    def add_message(self, role: str, content: str):
        """Add message to history with timestamp"""
        self.history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_session_duration(self) -> str:
        """Get formatted session duration"""
        if not self.start_time:
            return "0m"
        duration = datetime.now() - self.start_time
        minutes = int(duration.total_seconds() // 60)
        hours = minutes // 60
        minutes = minutes % 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"
    
    def get_message_count(self) -> int:
        """Get total number of messages exchanged"""
        return len(self.history)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for saving"""
        return {
            **asdict(self),
            "start_time": self.start_time.isoformat() if self.start_time else None
        }

class AllTalkTTS:
    """Handler for AllTalk TTS v2"""
    
    @staticmethod
    def check_tts_available() -> bool:
        """Check if AllTalk TTS is available"""
        try:
            url = f'{CONFIG["ALLTALK_TTS_URL"].rstrip("/")}/api/ready'
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status == 200
        except:
            return False
    
    @staticmethod
    def list_voices() -> List[str]:
        """Get list of available voices from AllTalk TTS"""
        try:
            url = f'{CONFIG["ALLTALK_TTS_URL"].rstrip("/")}/api/voices'
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=10) as resp:
                response_data = resp.read().decode("utf-8")
                data = json.loads(response_data)
                # Handle different response formats
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and "voices" in data:
                    return data["voices"]
                elif isinstance(data, dict) and "cloned_voices" in data:
                    # Combine cloned and preloaded voices
                    voices = data.get("cloned_voices", [])
                    if "preloaded_voices" in data:
                        voices.extend(data["preloaded_voices"])
                    return voices
                else:
                    console.print("[yellow]Warning: Could not parse voices list[/yellow]")
                    return ["default"]
        except Exception as e:
            console.print(f"[yellow]Warning: Could not fetch voices: {e}[/yellow]")
            return ["default"]
    
    @staticmethod
    def speak_text(text: str, voice: str, url: Optional[str] = None) -> bool:
        """
        Speak text using AllTalk TTS
        Args:
            text: Text to speak
            voice: Voice to use
            url: Optional custom TTS URL
        Returns:
            bool: Success status
        """
        tts_url = url or CONFIG["ALLTALK_TTS_URL"]
        # Clean up text for TTS
        # Remove markdown and special formatting
        tts_text = re.sub(r'[*_`#]', '', text)
        tts_text = re.sub(r'\[.*?\]\(.*?\)', '', tts_text)  # Remove markdown links
        tts_text = re.sub(r'\n+', '. ', tts_text)  # Replace newlines with periods
        tts_text = tts_text.strip()
        
        if not tts_text:
            return False
        
        try:
            endpoint = f'{tts_url.rstrip("/")}/api/tts'
            payload = {
                "text": tts_text,
                "voice": voice,
                "language": "en",
                "speed": 1.0,
                "stream": True
            }
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                endpoint,
                data=data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            
            # Start TTS in a separate thread to avoid blocking
            def _speak_thread():
                try:
                    with urllib.request.urlopen(req, timeout=CONFIG["REQUEST_TIMEOUT"]) as response:
                        # We don't need to read the response, just trigger the TTS
                        pass
                except Exception as e:
                    console.print(f"[dim]TTS Error: {e}[/dim]")
            
            thread = threading.Thread(target=_speak_thread, daemon=True)
            thread.start()
            return True
        except Exception as e:
            console.print(f"[dim]TTS Error: {e}[/dim]")
            return False

class OllamaAPI:
    """Wrapper for Ollama API with better error handling"""
    
    @staticmethod
    def http_request(url: str, method: str = "GET", data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request with comprehensive error handling"""
        headers = {"Accept": "application/json"}
        if data:
            headers["Content-Type"] = "application/json"
            data_bytes = json.dumps(data).encode("utf-8")
        else:
            data_bytes = None
        
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers=headers,
            method=method
        )
        
        try:
            with urllib.request.urlopen(req, timeout=CONFIG["REQUEST_TIMEOUT"]) as resp:
                response_data = resp.read().decode("utf-8")
                return json.loads(response_data)
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"HTTP Error {e.code}: {e.reason}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Connection Error: {e.reason}. Is Ollama running?")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid JSON response: {e}")
        except Exception as e:
            raise RuntimeError(f"Request failed: {e}")
    
    @classmethod
    def list_models(cls) -> List[str]:
        """Get list of available models with fallback methods"""
        models = []
        # Method 1: API endpoint
        try:
            data = cls.http_request(f'{CONFIG["OLLAMA_URL"].rstrip("/")}/api/tags')
            if isinstance(data, dict) and "models" in data:
                for model in data["models"]:
                    if name := model.get("name"):
                        models.append(name)
        except Exception:
            pass
        
        # Method 2: CLI fallback
        if not models:
            for cmd in [["ollama", "list", "--json"], ["ollama", "list"]]:
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        output = result.stdout
                        if "--json" in cmd:
                            for line in output.splitlines():
                                if line.strip():
                                    try:
                                        obj = json.loads(line)
                                        if "name" in obj:
                                            models.append(obj["name"])
                                    except json.JSONDecodeError:
                                        continue
                        else:
                            lines = output.splitlines()
                            for line in lines[1:]:  # Skip header
                                if parts := line.split():
                                    models.append(parts[0])
                        if models:
                            break
                except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
                    continue
        
        return sorted(set(models))
    
    @classmethod
    def generate(cls, model: str, prompt: str) -> str:
        """Generate text with streaming feedback"""
        url = f'{CONFIG["OLLAMA_URL"].rstrip("/")}/api/generate'
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.8,
                "stop": STOP_TOKENS,
                "num_ctx": 4096,
                "top_p": 0.9,
                "num_predict": 250,
                "frequency_penalty": 0.5,
                "presence_penalty": 0.5,
            },
        }
        
        try:
            data = cls.http_request(url, method="POST", data=payload)
            response = data.get("response", "").strip()
            
            # Clean up stop tokens
            for token in STOP_TOKENS:
                if token in response:
                    response = response.split(token)[0].strip()
            
            return cls.enhance_response(response)
        except RuntimeError as e:
            # Check if model exists
            if "not found" in str(e).lower():
                raise RuntimeError(f"Model '{model}' not found. Available models: {', '.join(cls.list_models()[:5])}...")
            raise
    
    @staticmethod
    def enhance_response(response: str) -> str:
        """Enhance AI response for better action-dependency"""
        # Remove common AI filler phrases
        filler_phrases = [
            "As you ",
            "You see that ",
            "It appears that ",
            "It seems that ",
            "You notice that ",
            "You realize that ",
            "Suddenly, ",
            "Without warning, ",
            "Out of nowhere, ",
        ]
        for phrase in filler_phrases:
            if response.lower().startswith(phrase.lower()):
                response = response[len(phrase):].capitalize()
        
        # Ensure response is direct and action-focused
        lines = response.split('. ')
        if len(lines) > 4:
            response = '. '.join(lines[:4]) + '.'
        
        # Remove passive voice where possible
        response = response.replace(" is seen ", " appears ")
        response = response.replace(" can be heard ", " sounds ")
        response = response.replace(" is felt ", " feels ")
        
        # Ensure consequence-first structure
        if response.lower().startswith(("you ", "i ")):
            # Try to rephrase to start with action consequence
            words = response.split()
            if len(words) > 3 and words[2].lower() in ["see", "notice", "feel", "hear"]:
                # Skip "You see/notice/feel/hear" constructions
                response = ' '.join(words[3:]).capitalize()
        
        return response.strip()

class ActionAnalyzer:
    """Analyzes player actions to improve AI responses"""
    
    @staticmethod
    def analyze_action(action: str, genre: str, role: str) -> Dict[str, Any]:
        """Analyze the player's action to extract key elements"""
        action_lower = action.lower()
        
        # Extract verbs and objects
        verbs = []
        objects = []
        targets = []
        
        # Common action verbs
        action_verbs = ["attack", "cast", "use", "open", "close", "take", "grab", "throw",
                        "run", "walk", "jump", "climb", "hide", "search", "look", "listen",
                        "talk", "ask", "tell", "persuade", "intimidate", "steal", "pick",
                        "lock", "unlock", "break", "destroy", "build", "create", "write",
                        "read", "study", "meditate", "pray", "summon", "banish", "heal",
                        "cure", "poison", "drink", "eat", "cook", "forge", "craft", "dodge",
                        "parry", "block", "defend", "charge", "sneak", "creep", "crawl"]
        
        # Common objects
        common_objects = ["sword", "shield", "door", "window", "chest", "book", "scroll",
                          "potion", "key", "lock", "trap", "monster", "enemy", "ally",
                          "npc", "character", "item", "weapon", "armor", "tool", "food",
                          "gold", "coin", "gem", "artifact", "relic", "altar", "shrine",
                          "wall", "floor", "ceiling", "ground", "tree", "rock", "bush"]
        
        # Extract verbs
        for verb in action_verbs:
            if verb in action_lower:
                verbs.append(verb)
        
        # Extract objects
        for obj in common_objects:
            if obj in action_lower:
                objects.append(obj)
        
        # Determine action type
        action_type = "other"
        if any(v in action_lower for v in ["attack", "fight", "kill", "stab", "shoot", "hit", "punch", "kick", "slash"]):
            action_type = "combat"
        elif any(v in action_lower for v in ["cast", "spell", "magic", "enchant", "summon", "banish", "curse", "bless"]):
            action_type = "magic"
        elif any(v in action_lower for v in ["talk", "speak", "ask", "tell", "persuade", "intimidate", "charm", "deceive"]):
            action_type = "social"
        elif any(v in action_lower for v in ["search", "look", "examine", "investigate", "inspect", "scan"]):
            action_type = "investigation"
        elif any(v in action_lower for v in ["open", "close", "lock", "unlock", "pick"]):
            action_type = "manipulation"
        elif any(v in action_lower for v in ["run", "walk", "jump", "climb", "hide", "sneak", "creep", "crawl", "dodge"]):
            action_type = "movement"
        elif any(v in action_lower for v in ["drink", "eat", "consume", "ingest"]):
            action_type = "consumption"
        
        # Determine intensity
        intensity = "medium"
        intense_words = ["violently", "forcefully", "powerfully", "fiercely", "aggressively",
                         "carefully", "cautiously", "gently", "quietly", "stealthily",
                         "desperately", "frantically", "calmly", "slowly", "quickly"]
        for word in intense_words:
            if word in action_lower:
                if word in ["violently", "forcefully", "powerfully", "fiercely", "aggressively", "desperately", "frantically"]:
                    intensity = "high"
                else:
                    intensity = "low"
                break
        
        # Determine success likelihood based on context
        success_likelihood = "possible"
        if any(w in action_lower for w in ["carefully", "expertly", "skillfully", "precisely"]):
            success_likelihood = "likely"
        elif any(w in action_lower for w in ["haphazardly", "clumsily", "recklessly", "randomly"]):
            success_likelihood = "unlikely"
        
        return {
            "verbs": verbs,
            "objects": objects,
            "type": action_type,
            "intensity": intensity,
            "success_likelihood": success_likelihood,
            "raw_action": action
        }
    
    @staticmethod
    def build_action_context(analysis: Dict[str, Any], genre: str, role: str) -> str:
        """Build context for the AI based on action analysis"""
        context = []
        
        # Add genre-specific context
        if genre == "Fantasy":
            if analysis["type"] == "magic":
                context.append("Magic exists and follows consistent rules. Spell effects are immediate and visible.")
            elif analysis["type"] == "combat":
                context.append("Combat involves medieval weapons and armor. Physics apply realistically.")
        elif genre == "Sci-Fi":
            if analysis["type"] == "combat":
                context.append("Combat involves energy weapons and advanced technology. Shields may absorb damage.")
            context.append("Technology is advanced but can malfunction under stress.")
        elif genre == "Cyberpunk":
            context.append("Technology is advanced but often glitchy. Corporations have immense power. Cyberware can fail catastrophically.")
        elif genre == "Post-Apocalyptic":
            context.append("Resources are scarce. Equipment is often damaged or makeshift. Every action has survival consequences.")
        
        # Add role-specific context
        if role in ["Mage", "Wizard", "Sorcerer", "Warlock"] and analysis["type"] == "magic":
            context.append(f"As a {role}, your magical abilities are specialized but require concentration.")
        elif role in ["Knight", "Warrior", "Soldier", "Gladiator"] and analysis["type"] == "combat":
            context.append(f"As a {role}, you are trained in combat and can perform complex maneuvers.")
        elif role in ["Thief", "Rogue", "Assassin", "Scout"]:
            context.append(f"As a {role}, you are skilled in stealth and subtlety. Your actions are precise and quiet.")
        elif role in ["Bard", "Diplomat", "Merchant"]:
            context.append(f"As a {role}, your words carry weight and can influence others significantly.")
        
        # Add action-specific context
        if analysis["intensity"] == "high":
            context.append("The action is performed with great force or intensity. Consequences will be dramatic.")
        elif analysis["intensity"] == "low":
            context.append("The action is performed carefully or subtly. Consequences will be nuanced.")
        
        if analysis["type"] == "social":
            context.append("Social interactions can influence NPC attitudes and relationships. Success depends on approach.")
        elif analysis["type"] == "combat":
            context.append("Combat actions have immediate physical consequences. Success depends on skill and circumstance.")
        elif analysis["type"] == "magic":
            context.append("Magic has tangible effects but may drain energy or attract unwanted attention.")
        
        # Add success likelihood context
        if analysis["success_likelihood"] == "likely":
            context.append("This action has a high chance of success given your approach.")
        elif analysis["success_likelihood"] == "unlikely":
            context.append("This action has a low chance of success given your haphazard approach.")
        
        return " ".join(context) if context else ""

class AdventureUI:
    """User Interface handler using Rich"""
    
    @staticmethod
    def show_title():
        """Display title screen"""
        title = Text("🧙 LLM Adventure Game 🗡️", style="bold magenta")
        subtitle = Text("Powered by Ollama", style="dim italic")
        console.print(Panel(
            title + "\n" + subtitle,
            border_style="cyan",
            padding=(1, 2)
        ))
    
    @staticmethod
    def show_commands():
        """Display available commands"""
        commands_table = Table(title="Available Commands", show_header=False, box=None)
        commands_table.add_column("Command", style="cyan", no_wrap=True)
        commands_table.add_column("Description", style="white")
        
        commands = [
            ("/quit, /exit", "Exit the game"),
            ("/restart", "Start a new game"),
            ("/save", "Save current game state (JSON)"),
            ("/load", "Load saved game"),
            ("/export_txt", "Export adventure as text file"),
            ("/history", "Show recent history"),
            ("/stats", "Show game statistics"),
            ("/redo", "🔄 Redo last action with NEW consequences"),
            ("/tts_on", "Enable TTS for world responses"),
            ("/tts_off", "Disable TTS"),
            ("/tts_voice", "Change TTS voice"),
            ("/help", "Show this help")
        ]
        
        for cmd, desc in commands:
            commands_table.add_row(cmd, desc)
        
        console.print(commands_table)
        console.print("\n[dim]💡 Pro Tip: Be SPECIFIC with actions! 'I carefully pick the lock with my dagger' works better than 'open door'[/dim]\n")
    
    @staticmethod
    def choose_option(title: str, options: List[str], description: str = "") -> str:
        """Interactive option selection"""
        table = Table(title=title, show_header=False, box=None)
        table.add_column("#", style="cyan", no_wrap=True)
        table.add_column("Option", style="white")
        
        for idx, option in enumerate(options, 1):
            table.add_row(str(idx), option)
        
        console.print(table)
        
        while True:
            try:
                choice = IntPrompt.ask(
                    f"[cyan]Select (1-{len(options)})[/cyan]",
                    show_default=False
                )
                if 1 <= choice <= len(options):
                    return options[choice - 1]
                console.print(f"[yellow]Please enter a number between 1 and {len(options)}[/yellow]")
            except ValueError:
                console.print("[yellow]Please enter a valid number[/yellow]")
    
    @staticmethod
    def show_loading(message: str = "Loading..."):
        """Show loading spinner"""
        with console.status(f"[cyan]{message}[/cyan]", spinner="dots"):
            time.sleep(0.5)
    
    @staticmethod
    def show_game_info(state: GameState):
        """Display current game information"""
        tts_status = "ON" if state.use_tts else "OFF"
        tts_voice_info = f" ({state.tts_voice})" if state.use_tts and state.tts_voice else ""
        
        info_panel = Panel(
            f"[bold]Genre:[/bold] {state.genre}\n"
            f"[bold]Role:[/bold] {state.role}\n"
            f"[bold]Player:[/bold] {state.player_name}\n"
            f"[bold]Model:[/bold] {state.model}\n"
            f"[bold]TTS:[/bold] {tts_status}{tts_voice_info}\n"
            f"[bold]Duration:[/bold] {state.get_session_duration()}\n"
            f"[bold]Actions:[/bold] {state.get_message_count() // 2}",
            title="Game Info",
            border_style="green"
        )
        console.print(info_panel)
    
    @staticmethod
    def show_world_response(text: str, use_tts: bool = False, tts_voice: Optional[str] = None):
        """Display world response with nice formatting"""
        console.print(f"\n[bold cyan]🌍 World Response 🌍[/bold cyan]")
        console.print(Markdown(text))
        
        # Speak the text if TTS is enabled
        if use_tts and tts_voice:
            AllTalkTTS.speak_text(text, tts_voice)
        
        console.print()
    
    @staticmethod
    def show_error(message: str):
        """Display error message"""
        console.print(f"[bold red]Error:[/bold red] {message}")
    
    @staticmethod
    def show_success(message: str):
        """Display success message"""
        console.print(f"[bold green]✅ {message}[/bold green]")
    
    @staticmethod
    def show_info(message: str):
        """Display info message"""
        console.print(f"[cyan]ℹ️ {message}[/cyan]")
    
    @staticmethod
    def show_action_analysis(analysis: Dict[str, Any]):
        """Display action analysis (for debugging)"""
        if analysis["verbs"] or analysis["objects"]:
            intensity_icon = "⚡" if analysis["intensity"] == "high" else "🐢" if analysis["intensity"] == "low" else "➡️"
            console.print(f"[dim]{intensity_icon} Action: {analysis['type']} ({analysis['intensity']} intensity) | Verbs: {', '.join(analysis['verbs'][:3]) or 'none'}[/dim]")

class AdventureExporter:
    """Handles exporting adventures to various formats"""
    
    @staticmethod
    def ensure_directories():
        """Create necessary directories if they don't exist"""
        for directory in [CONFIG["SAVE_DIR"], CONFIG["EXPORT_DIR"]]:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def export_to_txt(state: GameState, filename: Optional[str] = None) -> str:
        """
        Export adventure to a readable text file
        Returns: Path to the exported file
        """
        AdventureExporter.ensure_directories()
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = "".join(c for c in state.player_name if c.isalnum() or c in (' ', '-', '_'))
            filename = f"{safe_name}_{state.genre}_{timestamp}.txt"
        
        # Ensure .txt extension
        if not filename.endswith('.txt'):
            filename += '.txt'
        
        filepath = Path(CONFIG["EXPORT_DIR"]) / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                # Write header
                f.write("=" * 80 + "\n")
                f.write("ADVENTURE LOG\n")
                f.write("=" * 80 + "\n")
                
                # Metadata
                f.write("METADATA\n")
                f.write("-" * 40 + "\n")
                f.write(f"Player: {state.player_name}\n")
                f.write(f"Role: {state.role}\n")
                f.write(f"Genre: {state.genre}\n")
                f.write(f"Model: {state.model}\n")
                f.write(f"TTS Enabled: {state.use_tts}\n")
                if state.tts_voice:
                    f.write(f"TTS Voice: {state.tts_voice}\n")
                if state.start_time:
                    f.write(f"Started: {state.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Session Duration: {state.get_session_duration()}\n")
                f.write(f"Total Actions: {state.get_message_count() // 2}\n")
                f.write("\n")
                
                # Opening scene
                opener = ROLE_STARTERS.get(state.genre, {}).get(state.role,
                    "The atmosphere hangs with possibility when")
                f.write("OPENING SCENE\n")
                f.write("-" * 40 + "\n")
                f.write(f"{opener}...\n\n")
                
                # Adventure history
                f.write("ADVENTURE HISTORY\n")
                f.write("-" * 40 + "\n")
                
                # Group messages by action
                action_number = 1
                i = 0
                while i < len(state.history):
                    # Look for player message
                    if i < len(state.history) and state.history[i]["role"] == "user":
                        player_msg = state.history[i]
                        # Look for corresponding DM response
                        dm_response = ""
                        if i + 1 < len(state.history) and state.history[i + 1]["role"] == "assistant":
                            dm_response = state.history[i + 1]["content"]
                            i += 2
                        else:
                            i += 1
                        
                        # Write action
                        f.write(f"\nACTION #{action_number}\n")
                        f.write("~" * 40 + "\n")
                        f.write(f"[PLAYER]  {player_msg['content']}\n")
                        if dm_response:
                            f.write(f"[WORLD]   {dm_response}\n")
                        action_number += 1
                    else:
                        # Skip any non-user messages
                        i += 1
                
                # Footer
                f.write("\n" + "=" * 80 + "\n")
                f.write(f"End of adventure log\n")
                f.write(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 80 + "\n")
            
            return str(filepath)
        except Exception as e:
            raise RuntimeError(f"Failed to export adventure: {e}")

class GameManager:
    """Main game manager"""
    
    def __init__(self):
        self.state: Optional[GameState] = None
        self.ui = AdventureUI()
        self.exporter = AdventureExporter()
        self.analyzer = ActionAnalyzer()
        self.tts_available = False
    
    def setup_tts(self) -> Tuple[bool, Optional[str]]:
        """Setup TTS, returns (use_tts, tts_voice)"""
        console.print("\n[bold cyan]🔊 TTS Setup 🔊[/bold cyan]")
        
        # Check if AllTalk TTS is available
        with console.status("[cyan]Checking for AllTalk TTS...[/cyan]", spinner="dots"):
            self.tts_available = AllTalkTTS.check_tts_available()
        
        if not self.tts_available:
            console.print("[yellow]AllTalk TTS not found or not running.[/yellow]")
            console.print("[dim]Make sure AllTalk TTS v2 is running at:[/dim]")
            console.print(f"[dim]{CONFIG['ALLTALK_TTS_URL']}[/dim]")
            
            # Ask if user wants to enter custom URL
            if Confirm.ask("[cyan]Do you want to enter a custom TTS URL?[/cyan]", default=False):
                custom_url = Prompt.ask("[cyan]Enter TTS URL[/cyan]", default=CONFIG["ALLTALK_TTS_URL"])
                CONFIG["ALLTALK_TTS_URL"] = custom_url
                with console.status("[cyan]Checking custom TTS URL...[/cyan]", spinner="dots"):
                    self.tts_available = AllTalkTTS.check_tts_available()
            
            if not self.tts_available:
                console.print("[yellow]TTS will not be available for this session.[/yellow]")
                return False, None
        
        console.print("[green]✅ AllTalk TTS v2 is available[/green]")
        
        # Ask if user wants to use TTS
        use_tts = Confirm.ask("[cyan]Do you want to enable text-to-speech for world responses?[/cyan]", default=True)
        if not use_tts:
            return False, None
        
        # List available voices
        with console.status("[cyan]Loading available voices...[/cyan]", spinner="dots"):
            voices = AllTalkTTS.list_voices()
        
        if not voices:
            console.print("[yellow]No voices found. Using default voice.[/yellow]")
            return True, "default"
        
        # Let user choose a voice
        if len(voices) == 1:
            console.print(f"[cyan]Only one voice available: {voices[0]}[/cyan]")
            return True, voices[0]
        
        console.print(f"[cyan]Found {len(voices)} voices[/cyan]")
        voice = self.ui.choose_option("Select TTS Voice", voices)
        return True, voice
    
    def setup_game(self) -> bool:
        """Setup new game, returns True if setup successful"""
        self.ui.show_title()
        
        # Check Ollama availability
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                task = progress.add_task("Checking Ollama...", total=None)
                models = OllamaAPI.list_models()
                if not models:
                    self.ui.show_error("No Ollama models found. Please pull a model first:")
                    console.print("  [cyan]ollama pull llama3.1[/cyan]")
                    return False
                console.print(f"[green]✅ Found {len(models)} models[/green]")
        except RuntimeError as e:
            self.ui.show_error(str(e))
            console.print("\n[yellow]Make sure Ollama is running:[/yellow]")
            console.print("  [cyan]ollama serve[/cyan]")
            return False
        
        # Model selection
        model = self.ui.choose_option("Select Model", models)
        
        # TTS setup
        use_tts, tts_voice = self.setup_tts()
        
        # Character setup
        console.print("\n[bold cyan]🎭 Character Creation 🎭[/bold cyan]")
        player_name = Prompt.ask("[cyan]Character name[/cyan]", default="Adventurer")
        
        # Genre selection
        genres = list(ROLE_STARTERS.keys())
        genre = self.ui.choose_option("Select Genre", genres)
        
        # Role selection
        roles = list(ROLE_STARTERS[genre].keys())
        roles.append("Custom Role")
        role = self.ui.choose_option(f"Select Role for {genre}", roles)
        if role == "Custom Role":
            role = Prompt.ask("[cyan]Enter custom role[/cyan]", default="Adventurer")
        
        # Show game description
        desc = GENRE_DESCRIPTIONS.get(genre, "")
        if desc:
            console.print(Panel(desc, title=f"{genre} Setting", border_style="blue"))
        
        self.state = GameState(
            model=model,
            player_name=player_name,
            genre=genre,
            role=role,
            history=[],
            use_tts=use_tts,
            tts_voice=tts_voice
        )
        
        return True
    
    def build_prompt(self, user_action: str) -> str:
        """Build the prompt for the model with action analysis"""
        if not self.state:
            raise ValueError("Game state not initialized")
        
        # Analyze the action
        action_analysis = self.analyzer.analyze_action(user_action, self.state.genre, self.state.role)
        action_context = self.analyzer.build_action_context(action_analysis, self.state.genre, self.state.role)
        
        # Show analysis (for debugging/transparency)
        self.ui.show_action_analysis(action_analysis)
        
        # Start with system prompt
        system_context = (
            DM_SYSTEM_PROMPT.strip() + "\n" +
            ACTION_ANALYSIS_PROMPT.strip() + "\n" +
            f"CONTEXT:\n" +
            f"- Genre: {self.state.genre}\n" +
            f"- Character: {self.state.player_name} as {self.state.role}\n" +
            f"- Action Type: {action_analysis['type'].upper()}\n" +
            f"- Action Intensity: {action_analysis['intensity'].upper()}\n" +
            f"- Success Likelihood: {action_analysis['success_likelihood'].upper()}\n"
        )
        
        if action_context:
            system_context += f"- Additional Context: {action_context}\n"
        
        system_context += "\nCURRENT ACTION ANALYSIS:\n"
        if action_analysis['verbs']:
            system_context += f"- Key Verbs: {', '.join(action_analysis['verbs'])}\n"
        if action_analysis['objects']:
            system_context += f"- Key Objects: {', '.join(action_analysis['objects'])}\n"
        
        system_context += "\nRESPONSE REQUIREMENTS:\n"
        system_context += "1. EVERY sentence must directly relate to the player's SPECIFIC action\n"
        system_context += "2. Show PHYSICAL/LOGICAL consequences (not just 'you try')\n"
        system_context += "3. NO unrelated events or characters appearing out of nowhere\n"
        system_context += "4. 2-4 sentences MAXIMUM\n"
        system_context += "5. START with the direct consequence of the action\n"
        system_context += "6. Use ACTIVE voice to emphasize player agency\n"
        
        # Check if this is the first action
        if len(self.state.history) == 0:
            opener = ROLE_STARTERS.get(self.state.genre, {}).get(self.state.role,
                "The atmosphere hangs with possibility when")
            system_context += f"\nSCENE START: {opener}...\n"
        
        # Build history (last 3-4 actions for context)
        history_text = ""
        recent_history = self.state.history[-8:]  # Keep last 4 actions (player + DM pairs)
        for msg in recent_history:
            if msg["role"] == "user":
                history_text += f"PREVIOUS ACTION: {msg['content']}\n"
            elif msg["role"] == "assistant":
                history_text += f"RESULT: {msg['content']}\n"
        
        # Current action
        current_action = f"CURRENT ACTION: {user_action}\n"
        
        # Combine everything
        full_prompt = f"SYSTEM INSTRUCTIONS:\n{system_context}\n"
        if history_text:
            full_prompt += f"RECENT HISTORY:\n{history_text}\n"
        full_prompt += f"\n{current_action}\n"
        full_prompt += "NARRATE IMMEDIATE CONSEQUENCES (2-4 sentences, consequence-first):\n"
        
        return full_prompt
    
    def handle_command(self, command: str) -> bool:
        """Handle special commands, returns True if should continue"""
        cmd = command.strip().lower()
        
        if cmd in ("/quit", "/exit", "quit", "exit"):
            console.print("\n[bold green]Thanks for playing![/bold green]")
            return False
        elif cmd == "/restart":
            if Confirm.ask("[yellow]Restart game?[/yellow]"):
                console.print("\n[cyan]Starting new game...[/cyan]\n")
                return self.run()
        elif cmd == "/help":
            self.ui.show_commands()
        elif cmd == "/history":
            self.show_history()
        elif cmd == "/stats":
            self.show_stats()
        elif cmd == "/save":
            self.save_game()
        elif cmd == "/load":
            self.load_game()
        elif cmd == "/export_txt":
            self.export_adventure()
        elif cmd == "/redo":
            return self.redo_last_action()
        elif cmd == "/tts_on":
            if not self.tts_available:
                self.ui.show_error("TTS is not available. Make sure AllTalk TTS is running.")
            elif self.state:
                self.state.use_tts = True
                self.ui.show_success("TTS enabled for world responses")
            else:
                self.ui.show_error("No game in progress")
        elif cmd == "/tts_off":
            if self.state:
                self.state.use_tts = False
                self.ui.show_success("TTS disabled")
            else:
                self.ui.show_error("No game in progress")
        elif cmd == "/tts_voice":
            if not self.tts_available:
                self.ui.show_error("TTS is not available")
            elif self.state:
                self.change_tts_voice()
            else:
                self.ui.show_error("No game in progress")
        else:
            console.print(f"[yellow]Unknown command: {command}[/yellow]")
            console.print("Type /help for available commands")
        
        return True
    
    def redo_last_action(self) -> bool:
        """Redo the last action with a new response - core feature for exploring narrative branches"""
        if not self.state:
            console.print("[yellow]No game in progress[/yellow]")
            return True
        
        # Check if there's at least one player action and response to redo
        if len(self.state.history) < 2:
            console.print("[yellow]Nothing to redo yet[/yellow]")
            return True
        
        # Get the last player action (must be a user message)
        last_player_action = None
        last_response_index = None
        
        # Walk backwards to find the last user action followed by assistant response
        for i in range(len(self.state.history) - 1, 0, -1):
            if (self.state.history[i]["role"] == "assistant" and 
                self.state.history[i-1]["role"] == "user"):
                last_player_action = self.state.history[i-1]["content"]
                last_response_index = i
                break
        
        if not last_player_action:
            console.print("[yellow]No previous action-response pair found to redo[/yellow]")
            return True
        
        # Show the action being redone
        console.print(f"\n[cyan]🔄 Redoing last action:[/cyan] [bold]{last_player_action}[/bold]")
        
        # Remove the last response (and any subsequent messages if they exist)
        removed_count = 0
        while self.state.history and self.state.history[-1]["role"] == "assistant":
            self.state.history.pop()
            removed_count += 1
            # Only remove one response (the immediate one after player action)
            break
        
        if removed_count == 0:
            console.print("[yellow]No previous response to redo[/yellow]")
            return True
        
        console.print("[cyan]Generating new narrative consequences...[/cyan]")
        
        # Generate new response with fresh randomness
        with console.status("[bold cyan]The world reacts differently to your action...[/bold cyan]", spinner="dots"):
            prompt = self.build_prompt(last_player_action)
            response = OllamaAPI.generate(self.state.model, prompt)
        
        # Add the new response to history
        self.state.add_message("assistant", response)
        
        # Show the new response with special redo indicator
        console.print("\n[bold magenta]🔄 NEW CONSEQUENCES 🔄[/bold magenta]")
        self.ui.show_world_response(response, self.state.use_tts, self.state.tts_voice)
        
        return True
    
    def show_history(self):
        """Show recent game history"""
        if not self.state or not self.state.history:
            console.print("[yellow]No history yet[/yellow]")
            return
        
        history_table = Table(title="Recent History", show_header=True)
        history_table.add_column("#", style="cyan", no_wrap=True)
        history_table.add_column("Role", style="green", no_wrap=True)
        history_table.add_column("Content", style="white")
        
        # Show last 10 messages with simple numbering
        for i, msg in enumerate(self.state.history[-10:], 1):
            role_display = "👤 Player" if msg["role"] == "user" else "🌍 World"
            # Truncate long content
            content = msg["content"]
            if len(content) > 80:
                content = content[:77] + "..."
            history_table.add_row(str(i), role_display, content)
        
        console.print(history_table)
    
    def show_stats(self):
        """Show game statistics"""
        if not self.state:
            console.print("[yellow]No game in progress[/yellow]")
            return
        
        action_count = self.state.get_message_count() // 2
        unique_verbs = set()
        unique_objects = set()
        
        # Analyze history for action diversity
        for msg in self.state.history:
            if msg["role"] == "user":
                analysis = self.analyzer.analyze_action(msg["content"], self.state.genre, self.state.role)
                unique_verbs.update(analysis["verbs"])
                unique_objects.update(analysis["objects"])
        
        stats_panel = Panel(
            f"[bold]Session Duration:[/bold] {self.state.get_session_duration()}\n"
            f"[bold]Model:[/bold] {self.state.model}\n"
            f"[bold]TTS:[/bold] {'✅ ON' if self.state.use_tts else '❌ OFF'}\n"
            f"[bold]TTS Voice:[/bold] {self.state.tts_voice or 'N/A'}\n"
            f"[bold]Total Actions:[/bold] {action_count}\n"
            f"[bold]Unique Verbs Used:[/bold] {len(unique_verbs) or '0'}\n"
            f"[bold]Unique Objects Interacted:[/bold] {len(unique_objects) or '0'}\n"
            f"[bold]Genre:[/bold] {self.state.genre}\n"
            f"[bold]Role:[/bold] {self.state.role}",
            title="Game Statistics",
            border_style="yellow"
        )
        console.print(stats_panel)
    
    def save_game(self):
        """Save game state to JSON file"""
        if not self.state:
            console.print("[yellow]No game to save[/yellow]")
            return
        
        AdventureExporter.ensure_directories()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c for c in self.state.player_name if c.isalnum() or c in (' ', '-', '_'))
        default_filename = f"{safe_name}_{timestamp}.json"
        
        filename = Prompt.ask(
            "[cyan]Save filename[/cyan]",
            default=default_filename
        )
        if not filename.endswith('.json'):
            filename += '.json'
        
        filepath = Path(CONFIG["SAVE_DIR"]) / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.state.to_dict(), f, indent=2, ensure_ascii=False)
            self.ui.show_success(f"Game saved to {filepath}")
        except Exception as e:
            self.ui.show_error(f"Error saving game: {e}")
    
    def load_game(self):
        """Load game state from JSON file"""
        AdventureExporter.ensure_directories()
        
        # List available saves
        save_dir = Path(CONFIG["SAVE_DIR"])
        saves = []
        if save_dir.exists():
            saves = [f.name for f in save_dir.glob("*.json")]
        
        if not saves:
            console.print("[yellow]No saved games found[/yellow]")
            return
        
        # Let user choose a save file
        console.print("\n[bold cyan]Available Saves:[/bold cyan]")
        for i, save in enumerate(saves, 1):
            console.print(f"  [{i}] {save}")
        
        try:
            choice = IntPrompt.ask(
                f"[cyan]Select save (1-{len(saves)}) or 0 to enter filename[/cyan]",
                show_default=False
            )
            if choice == 0:
                filename = Prompt.ask("[cyan]Enter filename[/cyan]")
            else:
                if 1 <= choice <= len(saves):
                    filename = saves[choice - 1]
                else:
                    console.print("[yellow]Invalid selection[/yellow]")
                    return
        except ValueError:
            filename = Prompt.ask("[cyan]Enter filename[/cyan]")
        
        filepath = Path(CONFIG["SAVE_DIR"]) / filename
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate loaded data
            required = ["model", "player_name", "genre", "role", "history"]
            if not all(k in data for k in required):
                raise ValueError("Invalid save file format")
            
            # Check TTS availability if it was enabled
            if data.get("use_tts", False):
                with console.status("[cyan]Checking TTS...[/cyan]", spinner="dots"):
                    self.tts_available = AllTalkTTS.check_tts_available()
                if not self.tts_available:
                    console.print("[yellow]TTS was enabled in save but is not currently available[/yellow]")
                    data["use_tts"] = False
            
            self.state = GameState(
                model=data["model"],
                player_name=data["player_name"],
                genre=data["genre"],
                role=data["role"],
                history=data["history"],
                use_tts=data.get("use_tts", False),
                tts_voice=data.get("tts_voice"),
                start_time=datetime.fromisoformat(data["start_time"]) if data.get("start_time") else None
            )
            self.ui.show_success(f"Game loaded from {filepath}")
            self.ui.show_game_info(self.state)
        except FileNotFoundError:
            self.ui.show_error(f"File not found: {filepath}")
        except Exception as e:
            self.ui.show_error(f"Error loading game: {e}")
    
    def export_adventure(self):
        """Export adventure to text format"""
        if not self.state:
            console.print("[yellow]No game to export[/yellow]")
            return
        
        # Get filename base
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c for c in self.state.player_name if c.isalnum() or c in (' ', '-', '_'))
        default_base = f"{safe_name}_{self.state.genre}_{timestamp}"
        
        base_filename = Prompt.ask(
            "[cyan]Filename[/cyan]",
            default=default_base
        )
        if not base_filename.endswith('.txt'):
            base_filename += '.txt'
        
        try:
            txt_file = self.exporter.export_to_txt(self.state, base_filename)
            console.print(f"[green]✅ Adventure exported to: {txt_file}[/green]")
            
            # Offer to open the file
            if Confirm.ask("[cyan]Open exported file?[/cyan]", default=False):
                try:
                    import subprocess
                    import platform
                    filepath = txt_file
                    system = platform.system()
                    if system == "Darwin":  # macOS
                        subprocess.run(["open", filepath])
                    elif system == "Windows":
                        os.startfile(filepath)
                    elif system == "Linux":
                        subprocess.run(["xdg-open", filepath])
                except Exception as e:
                    console.print(f"[yellow]Could not open file: {e}[/yellow]")
        except Exception as e:
            self.ui.show_error(f"Export failed: {e}")
    
    def change_tts_voice(self):
        """Change the current TTS voice"""
        if not self.tts_available:
            self.ui.show_error("TTS is not available")
            return
        
        with console.status("[cyan]Loading available voices...[/cyan]", spinner="dots"):
            voices = AllTalkTTS.list_voices()
        
        if not voices:
            self.ui.show_error("No voices found")
            return
        
        voice = self.ui.choose_option("Select TTS Voice", voices)
        if self.state:
            self.state.tts_voice = voice
            self.ui.show_success(f"TTS voice changed to: {voice}")
    
    def game_loop(self):
        """Main game loop - where story is shaped by player actions"""
        if not self.state:
            raise ValueError("Game not initialized")
        
        # Show opening scene
        opener = ROLE_STARTERS.get(self.state.genre, {}).get(self.state.role,
            "The atmosphere hangs with possibility when")
        console.print(Panel(
            f"[italic]{opener}...[/italic]",
            title="The Adventure Begins",
            border_style="cyan"
        ))
        console.print("[dim]Enter your action. Be SPECIFIC! Type /help for commands.[/dim]\n")
        
        # Main game loop
        while True:
            try:
                # Get player action
                action = Prompt.ask(
                    f"[bold cyan]Action »[/bold cyan] "
                ).strip()
                
                if not action:
                    continue
                
                # Check for commands
                if action.startswith('/'):
                    if not self.handle_command(action):
                        break
                    continue
                
                # Validate action (not too short)
                if len(action.split()) < 2:
                    console.print("[yellow]⚠️ Please be more specific with your action![/yellow]")
                    console.print("[dim]Example: 'I draw my sword and attack the orc' instead of 'attack'[/dim]")
                    continue
                
                # Add to history BEFORE generating response (so redo works correctly)
                self.state.add_message("user", action)
                
                # Generate response based STRICTLY on player's action
                with console.status("[bold cyan]The world reacts to your specific action...[/bold cyan]", spinner="dots"):
                    prompt = self.build_prompt(action)
                    response = OllamaAPI.generate(self.state.model, prompt)
                
                # Add response to history and display
                self.state.add_message("assistant", response)
                self.ui.show_world_response(response, self.state.use_tts, self.state.tts_voice)
                
                # Auto-save every 5 actions
                action_count = self.state.get_message_count() // 2
                if action_count % 5 == 0:
                    try:
                        AdventureExporter.ensure_directories()
                        autosave_path = Path(CONFIG["SAVE_DIR"]) / f"autosave_{self.state.player_name}.json"
                        with open(autosave_path, 'w', encoding='utf-8') as f:
                            json.dump(self.state.to_dict(), f, indent=2, ensure_ascii=False)
                        console.print(f"[dim]💾 Auto-saved (Action {action_count})[/dim]")
                    except:
                        pass  # Don't crash on autosave failure
            
            except KeyboardInterrupt:
                if Confirm.ask("\n[yellow]Really quit?[/yellow]"):
                    # Offer to save before quitting
                    if Confirm.ask("[cyan]Save game before quitting?[/cyan]", default=True):
                        self.save_game()
                    break
                console.print("\n[cyan]Resuming...[/cyan]")
                continue
            
            except RuntimeError as e:
                self.ui.show_error(str(e))
                if "model not found" in str(e).lower():
                    if Confirm.ask("[yellow]Choose different model?[/yellow]"):
                        return self.run()
                    else:
                        break
                continue
    
    def run(self) -> bool:
        """Run the game, returns True if should restart"""
        if not self.setup_game():
            return False
        
        self.ui.show_game_info(self.state)
        self.ui.show_commands()
        
        try:
            self.game_loop()
        except Exception as e:
            self.ui.show_error(f"Unexpected error: {e}")
            console.print_exception(show_locals=False)
        
        # Ask if player wants to restart
        if Confirm.ask("[cyan]Play again?[/cyan]", default=False):
            return True
        return False

def main():
    """Main entry point"""
    # Create necessary directories
    AdventureExporter.ensure_directories()
    
    game = GameManager()
    
    try:
        while True:
            if not game.run():
                break
            console.print("\n" + "="*50 + "\n")
    except KeyboardInterrupt:
        console.print("\n[yellow]Game interrupted[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]Fatal error:[/bold red] {e}")
        console.print_exception(show_locals=False)
    
    console.print("\n[bold green]Thanks for playing![/bold green]")

if __name__ == "__main__":
    main()