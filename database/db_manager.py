import sqlite3
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path="bot_database.db"):
        self.db_path = db_path
        self._create_tables()
        self._seed_data()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=10.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 5000")
        conn.execute("PRAGMA journal_mode = WAL")
        return conn
    
    def _create_tables(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                user_id TEXT PRIMARY KEY,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                messages INTEGER DEFAULT 0,
                commands_used INTEGER DEFAULT 0,
                inventory_slots INTEGER DEFAULT 10,
                titulo_ativo TEXT,
                bio TEXT,
                banner TEXT,
                embed_color TEXT DEFAULT '#3498db',
                created_at TEXT,
                last_seen TEXT,
                marriage_anniversary TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS titulos (
                titulo_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                titulo_nome TEXT,
                FOREIGN KEY (user_id) REFERENCES usuarios(user_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS timeline (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                event_type TEXT,
                description TEXT,
                timestamp TEXT,
                FOREIGN KEY (user_id) REFERENCES usuarios(user_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS missoes_coop (
                coop_id INTEGER PRIMARY KEY AUTOINCREMENT,
                leader_id TEXT,
                partner_id TEXT,
                mission_type TEXT,
                target_value INTEGER,
                current_value INTEGER DEFAULT 0,
                active INTEGER DEFAULT 1,
                FOREIGN KEY (leader_id) REFERENCES usuarios(user_id),
                FOREIGN KEY (partner_id) REFERENCES usuarios(user_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventario_historico (
                history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                item_name TEXT,
                action TEXT,
                timestamp TEXT,
                FOREIGN KEY (user_id) REFERENCES usuarios(user_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mercado_leiloes (
                auction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_id TEXT,
                item_name TEXT,
                current_bid INTEGER,
                highest_bidder_id TEXT,
                ends_at TEXT,
                active INTEGER DEFAULT 1,
                FOREIGN KEY (seller_id) REFERENCES usuarios(user_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS economia (
                user_id TEXT PRIMARY KEY,
                coins INTEGER DEFAULT 0,
                bank INTEGER DEFAULT 0,
                total_earned INTEGER DEFAULT 0,
                total_spent INTEGER DEFAULT 0,
                last_daily TEXT,
                last_work TEXT,
                debt INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES usuarios(user_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pets (
                pet_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                species TEXT,
                custom_name TEXT,
                level INTEGER DEFAULT 1,
                xp INTEGER DEFAULT 0,
                rarity TEXT DEFAULT 'comum',
                hunger INTEGER DEFAULT 100,
                happiness INTEGER DEFAULT 100,
                hygiene INTEGER DEFAULT 100,
                health INTEGER DEFAULT 100,
                evolution_stage INTEGER DEFAULT 0,
                adopted_at TEXT,
                last_fed TEXT,
                last_bath TEXT,
                last_play TEXT,
                last_update TEXT,
                passive_skill TEXT,
                FOREIGN KEY (user_id) REFERENCES usuarios(user_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS profissao_progresso (
                progress_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                profession_id INTEGER,
                level INTEGER DEFAULT 1,
                xp INTEGER DEFAULT 0,
                chosen_at TEXT,
                specialization TEXT,
                tools TEXT,
                FOREIGN KEY (user_id) REFERENCES usuarios(user_id),
                FOREIGN KEY (profession_id) REFERENCES profissoes(profession_id),
                UNIQUE(user_id, profession_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS profissoes (
                profession_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                description TEXT,
                icon TEXT,
                is_illegal INTEGER DEFAULT 0,
                unlocked_by TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS missoes (
                mission_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                description TEXT,
                mission_type TEXT,
                target_value INTEGER,
                reward_type TEXT,
                reward_value INTEGER
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS missoes_progresso (
                progress_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                mission_id INTEGER,
                current_progress INTEGER DEFAULT 0,
                completed INTEGER DEFAULT 0,
                claimed INTEGER DEFAULT 0,
                started_at TEXT,
                completed_at TEXT,
                FOREIGN KEY (user_id) REFERENCES usuarios(user_id),
                FOREIGN KEY (mission_id) REFERENCES missoes(mission_id),
                UNIQUE(user_id, mission_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conquistas (
                achievement_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                description TEXT,
                icon TEXT,
                requirement_type TEXT,
                requirement_value INTEGER,
                reward_xp INTEGER DEFAULT 0,
                reward_coins INTEGER DEFAULT 0,
                secret INTEGER DEFAULT 0,
                rarity REAL DEFAULT 0.0,
                is_hidden INTEGER DEFAULT 0
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conquistas_usuario (
                unlock_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                achievement_id INTEGER,
                unlocked_at TEXT,
                FOREIGN KEY (user_id) REFERENCES usuarios(user_id),
                FOREIGN KEY (achievement_id) REFERENCES conquistas(achievement_id),
                UNIQUE(user_id, achievement_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventario (
                inventory_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                item_name TEXT,
                item_type TEXT,
                quantity INTEGER DEFAULT 1,
                rarity TEXT DEFAULT 'comum',
                description TEXT,
                FOREIGN KEY (user_id) REFERENCES usuarios(user_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mercado (
                listing_id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_id TEXT,
                item_name TEXT,
                item_type TEXT,
                price INTEGER,
                quantity INTEGER DEFAULT 1,
                listed_at TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS warns (
                warn_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                guild_id TEXT,
                moderator_id TEXT,
                reason TEXT,
                warned_at TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS guild_config (
                guild_id TEXT PRIMARY KEY,
                log_channel_id TEXT,
                welcome_channel_id TEXT,
                prefix TEXT DEFAULT '!'
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS duelos_stats (
                user_id TEXT PRIMARY KEY,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES usuarios(user_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_stats (
                user_id TEXT PRIMARY KEY,
                correct_answers INTEGER DEFAULT 0,
                wrong_answers INTEGER DEFAULT 0,
                total_games INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES usuarios(user_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reputacao (
                user_id TEXT PRIMARY KEY,
                positive INTEGER DEFAULT 0,
                negative INTEGER DEFAULT 0,
                total INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES usuarios(user_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS forca_games (
                game_id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT,
                host_id TEXT,
                word TEXT,
                guessed_letters TEXT DEFAULT '',
                wrong_letters TEXT DEFAULT '',
                attempts_left INTEGER DEFAULT 6,
                players TEXT DEFAULT '',
                started_at TEXT,
                active INTEGER DEFAULT 1
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS level_notifications (
                user_id TEXT PRIMARY KEY,
                last_notified_level INTEGER DEFAULT 0,
                last_notification_time TEXT DEFAULT '',
                mention_disabled INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES usuarios(user_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS command_cooldowns (
                user_id TEXT,
                command_name TEXT,
                last_used TEXT,
                PRIMARY KEY (user_id, command_name),
                FOREIGN KEY (user_id) REFERENCES usuarios(user_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS boost_tracking (
                boost_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                boosted_at TEXT,
                FOREIGN KEY (user_id) REFERENCES usuarios(user_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS emprestimos (
                loan_id INTEGER PRIMARY KEY AUTOINCREMENT,
                lender_id TEXT,
                borrower_id TEXT,
                amount INTEGER,
                interest_rate REAL,
                due_at TEXT,
                status TEXT DEFAULT 'pending',
                FOREIGN KEY (lender_id) REFERENCES usuarios(user_id),
                FOREIGN KEY (borrower_id) REFERENCES usuarios(user_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS imoveis (
                property_id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id TEXT,
                name TEXT,
                price INTEGER,
                rent_value INTEGER,
                last_rent_claim TEXT,
                FOREIGN KEY (owner_id) REFERENCES usuarios(user_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _seed_data(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM profissoes")
        if cursor.fetchone()['count'] == 0:
            profissoes = [
                ('Cacador', 'Especialista em caca e coleta de recursos', '🏹'),
                ('Engenheiro', 'Especialista em fabricar e construir itens', '⚙️'),
                ('Alquimista', 'Especialista em pocoes e transmutacoes', '⚗️'),
                ('Chef', 'Especialista em culinaria e gastronomia', '👨‍🍳'),
                ('Comerciante', 'Especialista em negocios e comercio', '💼')
            ]
            cursor.executemany(
                "INSERT INTO profissoes (name, description, icon) VALUES (?, ?, ?)",
                profissoes
            )
        
        cursor.execute("SELECT COUNT(*) as count FROM missoes")
        if cursor.fetchone()['count'] == 0:
            missoes = [
                ('Mensageiro', 'Envie 50 mensagens', 'messages', 50, 'coins', 200),
                ('Trabalhador', 'Trabalhe 5 vezes', 'work', 5, 'coins', 300),
                ('Comandante', 'Use 20 comandos', 'commands', 20, 'xp', 150),
                ('Explorador', 'Complete 3 aventuras com pets', 'pet_adventure', 3, 'coins', 500),
                ('Colecionador', 'Consiga 5 pets', 'pets_total', 5, 'coins', 1000),
                ('Social', 'Faca 10 interacoes sociais', 'social', 10, 'xp', 200),
                ('Jogador', 'Jogue 10 mini-games', 'minigames', 10, 'coins', 400),
                ('Rico', 'Acumule 5000 moedas', 'coins_total', 5000, 'xp', 500)
            ]
            cursor.executemany(
                "INSERT INTO missoes (title, description, mission_type, target_value, reward_type, reward_value) VALUES (?, ?, ?, ?, ?, ?)",
                missoes
            )
        
        cursor.execute("SELECT COUNT(*) as count FROM conquistas")
        if cursor.fetchone()['count'] == 0:
            conquistas = [
                ('Iniciante', 'Alcancar nivel 5', '🌟', 'level', 5, 50, 100),
                ('Experiente', 'Alcancar nivel 10', '⭐', 'level', 10, 100, 250),
                ('Veterano', 'Alcancar nivel 25', '🏆', 'level', 25, 250, 500),
                ('Mestre', 'Alcancar nivel 50', '👑', 'level', 50, 500, 1000),
                ('Mensageiro', 'Enviar 100 mensagens', '💬', 'messages', 100, 50, 100),
                ('Comunicador', 'Enviar 500 mensagens', '📝', 'messages', 500, 100, 250),
                ('Tagarela', 'Enviar 1000 mensagens', '🗣️', 'messages', 1000, 200, 500),
                ('Rico', 'Ter 10000 moedas', '💰', 'coins', 10000, 100, 0),
                ('Milionario', 'Ter 100000 moedas', '💎', 'coins', 100000, 500, 0)
            ]
            cursor.executemany(
                "INSERT INTO conquistas (name, description, icon, requirement_type, requirement_value, reward_xp, reward_coins) VALUES (?, ?, ?, ?, ?, ?, ?)",
                conquistas
            )
        
        conn.commit()
        conn.close()
    
    def ensure_user_exists(self, user_id: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT 1 FROM usuarios WHERE user_id = ?", (user_id,))
        if not cursor.fetchone():
            now = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO usuarios (user_id, created_at, last_seen)
                VALUES (?, ?, ?)
            """, (user_id, now, now))
            
            cursor.execute("""
                INSERT INTO economia (user_id) VALUES (?)
            """, (user_id,))
            
            cursor.execute("""
                INSERT INTO duelos_stats (user_id) VALUES (?)
            """, (user_id,))
            
            cursor.execute("""
                INSERT INTO quiz_stats (user_id) VALUES (?)
            """, (user_id,))
            
            cursor.execute("""
                INSERT INTO reputacao (user_id) VALUES (?)
            """, (user_id,))
            
            conn.commit()
        
        conn.close()
