"""
Turn-based Combat System for Adventure Game CLI

This module provides a complete turn-based combat system with:
- Character and enemy classes with health, attack, defense stats
- Turn management and action selection
- Damage calculation with critical hits and defense
- Combat logging and status display
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import random


class ActionType(Enum):
    """Types of actions available in combat"""
    ATTACK = "attack"
    DEFEND = "defend"
    SPECIAL = "special"
    ITEM = "item"
    FLEE = "flee"


@dataclass
class CombatStats:
    """Data class for combat statistics"""
    max_health: int
    current_health: int
    attack_power: int
    defense: int
    speed: int
    critical_chance: float = 0.15  # 15% base chance
    special_attack_cooldown: int = 0

    def take_damage(self, damage: int) -> int:
        """Apply damage and return actual damage taken"""
        actual_damage = max(1, damage - (self.defense // 3))
        self.current_health = max(0, self.current_health - actual_damage)
        return actual_damage

    def heal(self, amount: int) -> int:
        """Heal and return actual healing done"""
        healing = min(amount, self.max_health - self.current_health)
        self.current_health += healing
        return healing

    def is_alive(self) -> bool:
        """Check if entity is still alive"""
        return self.current_health > 0

    def get_health_percentage(self) -> float:
        """Get current health as percentage"""
        return (self.current_health / self.max_health) * 100


class CombatEntity(ABC):
    """Abstract base class for all entities that can participate in combat"""

    def __init__(self, name: str, stats: CombatStats):
        self.name = name
        self.stats = stats
        self.is_defending = False
        self.action_history: List[str] = []

    @abstractmethod
    def choose_action(self, opponent: 'CombatEntity') -> Tuple[ActionType, dict]:
        """Choose next action in combat"""
        pass

    def attack(self, opponent: 'CombatEntity') -> Tuple[int, bool]:
        """Attack opponent and return damage and critical hit status"""
        base_damage = self.stats.attack_power + random.randint(-5, 5)
        is_critical = random.random() < self.stats.critical_chance

        if is_critical:
            base_damage = int(base_damage * 1.5)

        # Reduce damage if opponent is defending
        if opponent.is_defending:
            base_damage = int(base_damage * 0.6)

        damage_dealt = opponent.stats.take_damage(base_damage)
        return damage_dealt, is_critical

    def special_attack(self, opponent: 'CombatEntity') -> Tuple[int, bool]:
        """Perform a special attack with higher damage but cooldown"""
        if self.stats.special_attack_cooldown > 0:
            return 0, False

        base_damage = int(self.stats.attack_power * 1.8) + random.randint(0, 10)
        is_critical = random.random() < self.stats.critical_chance * 1.5

        if is_critical:
            base_damage = int(base_damage * 1.5)

        damage_dealt = opponent.stats.take_damage(base_damage)
        self.stats.special_attack_cooldown = 3  # 3 turn cooldown
        return damage_dealt, is_critical

    def defend(self) -> None:
        """Enter defensive stance"""
        self.is_defending = True

    def reset_turn(self) -> None:
        """Reset turn state"""
        self.is_defending = False
        if self.stats.special_attack_cooldown > 0:
            self.stats.special_attack_cooldown -= 1

    def get_status_string(self) -> str:
        """Get formatted status string"""
        health_pct = self.stats.get_health_percentage()
        health_bar = "█" * int(health_pct // 10) + "░" * (10 - int(health_pct // 10))
        status = f"[{health_bar}] {self.stats.current_health}/{self.stats.max_health} HP"
        if self.is_defending:
            status += " [DEFENDING]"
        if self.stats.special_attack_cooldown > 0:
            status += f" [SPECIAL: {self.stats.special_attack_cooldown}]"
        return status


class Player(CombatEntity):
    """Player character in combat"""

    def __init__(self, name: str, stats: CombatStats):
        super().__init__(name, stats)
        self.inventory: dict = {}
        self.available_actions = [ActionType.ATTACK, ActionType.DEFEND, ActionType.SPECIAL, ActionType.ITEM, ActionType.FLEE]

    def choose_action(self, opponent: 'CombatEntity') -> Tuple[ActionType, dict]:
        """Player chooses action (implement UI selection here)"""
        # This is a placeholder - in actual implementation, this would get player input
        action = random.choice([ActionType.ATTACK, ActionType.DEFEND, ActionType.SPECIAL])
        return action, {}

    def display_available_actions(self) -> None:
        """Display available actions to player"""
        print("\n--- Available Actions ---")
        for i, action in enumerate(self.available_actions, 1):
            if action == ActionType.SPECIAL and self.stats.special_attack_cooldown > 0:
                print(f"{i}. {action.value.upper()} (Cooldown: {self.stats.special_attack_cooldown})")
            else:
                print(f"{i}. {action.value.upper()}")


class Enemy(CombatEntity):
    """Enemy character in combat"""

    def __init__(self, name: str, stats: CombatStats, ai_difficulty: int = 1):
        super().__init__(name, stats)
        self.ai_difficulty = max(1, min(3, ai_difficulty))  # Clamp between 1-3
        self.action_pattern: List[ActionType] = []
        self.pattern_index = 0

    def choose_action(self, opponent: 'CombatEntity') -> Tuple[ActionType, dict]:
        """AI chooses action based on difficulty"""
        opponent_health_pct = opponent.stats.get_health_percentage()

        if self.ai_difficulty == 1:  # Easy
            actions = [ActionType.ATTACK] * 70 + [ActionType.DEFEND] * 30
        elif self.ai_difficulty == 2:  # Medium
            actions = [ActionType.ATTACK] * 60 + [ActionType.DEFEND] * 25 + [ActionType.SPECIAL] * 15
        else:  # Hard
            actions = [ActionType.ATTACK] * 50 + [ActionType.DEFEND] * 20 + [ActionType.SPECIAL] * 30

        # Strategic decisions based on health
        if self.stats.get_health_percentage() < 30:
            actions = [ActionType.DEFEND] * 50 + [ActionType.ATTACK] * 50

        action = random.choice(actions)
        return action, {}


class CombatSystem:
    """Main combat system managing turn-based battles"""

    def __init__(self, player: Player, enemy: Enemy):
        self.player = player
        self.enemy = enemy
        self.turn_count = 0
        self.combat_log: List[str] = []
        self.battle_active = True

    def determine_turn_order(self) -> List[CombatEntity]:
        """Determine who goes first based on speed"""
        entities = [self.player, self.enemy]
        # Higher speed goes first, with some randomness
        player_priority = self.player.stats.speed + random.randint(0, 10)
        enemy_priority = self.enemy.stats.speed + random.randint(0, 10)

        if player_priority >= enemy_priority:
            return entities
        else:
            return [self.enemy, self.player]

    def execute_action(self, actor: CombatEntity, opponent: CombatEntity, action: ActionType, action_data: dict) -> None:
        """Execute a combat action"""
        if action == ActionType.ATTACK:
            damage, is_critical = actor.attack(opponent)
            crit_text = " (CRITICAL HIT!)" if is_critical else ""
            log_entry = f"{actor.name} attacks {opponent.name} for {damage} damage{crit_text}"
            self.combat_log.append(log_entry)
            print(f"  → {log_entry}")

        elif action == ActionType.DEFEND:
            actor.defend()
            log_entry = f"{actor.name} takes a defensive stance!"
            self.combat_log.append(log_entry)
            print(f"  → {log_entry}")

        elif action == ActionType.SPECIAL:
            if actor.stats.special_attack_cooldown > 0:
                log_entry = f"{actor.name}'s special move is still on cooldown!"
                self.combat_log.append(log_entry)
                print(f"  → {log_entry}")
            else:
                damage, is_critical = actor.special_attack(opponent)
                crit_text = " (CRITICAL!)" if is_critical else ""
                log_entry = f"{actor.name} uses SPECIAL ATTACK on {opponent.name} for {damage} damage{crit_text}"
                self.combat_log.append(log_entry)
                print(f"  → {log_entry}")

        elif action == ActionType.ITEM:
            log_entry = f"{actor.name} uses an item!"
            self.combat_log.append(log_entry)
            print(f"  → {log_entry}")

        elif action == ActionType.FLEE:
            log_entry = f"{actor.name} attempts to flee!"
            self.combat_log.append(log_entry)
            print(f"  → {log_entry}")

    def display_status(self) -> None:
        """Display current combat status"""
        print("\n" + "="*50)
        print(f"TURN {self.turn_count}")
        print("="*50)
        print(f"{self.player.name}:  {self.player.get_status_string()}")
        print(f"{self.enemy.name}: {self.enemy.get_status_string()}")
        print("="*50)

    def execute_turn(self, player_action: Optional[Tuple[ActionType, dict]] = None) -> bool:
        """Execute one turn of combat"""
        if not self.battle_active:
            return False

        self.turn_count += 1
        print(f"\n{'='*50}")
        print(f"TURN {self.turn_count}")
        print(f"{'='*50}")

        # Reset turn states
        self.player.reset_turn()
        self.enemy.reset_turn()

        # Get actions
        if player_action is None:
            player_action = self.player.choose_action(self.enemy)
        enemy_action = self.enemy.choose_action(self.player)

        # Determine turn order and execute
        turn_order = self.determine_turn_order()

        for entity in turn_order:
            if entity == self.player:
                action, data = player_action
            else:
                action, data = enemy_action

            opponent = self.enemy if entity == self.player else self.player
            self.execute_action(entity, opponent, action, data)

            # Check if battle ended
            if not opponent.stats.is_alive():
                self.battle_active = False
                break

        self.display_status()
        return self.battle_active

    def start_battle(self, auto_play: bool = False) -> str:
        """Start and run the battle"""
        print(f"\n{'*'*50}")
        print(f"BATTLE START: {self.player.name} vs {self.enemy.name}")
        print(f"{'*'*50}\n")

        while self.battle_active:
            if auto_play:
                # AI controls both characters
                self.execute_turn()
            else:
                # Player makes decision
                self.player.display_available_actions()
                # In real implementation, get player input here
                self.execute_turn()

        return self.get_battle_result()

    def get_battle_result(self) -> str:
        """Determine and return battle result"""
        if self.player.stats.is_alive():
            result = f"\n{'*'*50}\n{self.player.name} WINS!\n{'*'*50}"
            self.combat_log.append(f"BATTLE WON: {self.player.name} defeated {self.enemy.name}")
            return result
        else:
            result = f"\n{'*'*50}\n{self.enemy.name} WINS!\n{'*'*50}"
            self.combat_log.append(f"BATTLE LOST: {self.enemy.name} defeated {self.player.name}")
            return result

    def get_combat_log(self) -> List[str]:
        """Return the combat log"""
        return self.combat_log


# Example usage
if __name__ == "__main__":
    # Create player
    player_stats = CombatStats(
        max_health=100,
        current_health=100,
        attack_power=15,
        defense=8,
        speed=10
    )
    player = Player("Hero", player_stats)

    # Create enemy
    enemy_stats = CombatStats(
        max_health=80,
        current_health=80,
        attack_power=12,
        defense=5,
        speed=9
    )
    enemy = Enemy("Goblin", enemy_stats, ai_difficulty=2)

    # Create and run combat
    combat = CombatSystem(player, enemy)
    result = combat.start_battle(auto_play=True)
    print(result)

    # Print battle log
    print("\n--- Combat Log ---")
    for log_entry in combat.get_combat_log():
        print(f"• {log_entry}")
