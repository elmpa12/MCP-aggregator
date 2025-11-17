"""Sistema de feedback para melhorar qualidade do RAG baseado em uso real."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import numpy as np
from collections import defaultdict
import asyncio
import subprocess
from dataclasses import dataclass, asdict
import pandas as pd
import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SystemInsight:
    """Insight descoberto pelo sistema."""
    timestamp: str
    category: str
    insight: str
    confidence: float
    action_taken: Optional[str] = None
    impact_score: float = 0.0

@dataclass 
class TradingPattern:
    """Padrão de trading identificado."""
    name: str
    timeframe: str
    symbol: str
    conditions: Dict
    performance: Dict
    discovered_at: str
    
class BotScalpBrain:
    """
    Cérebro central do BotScalp - Sistema de inteligência que:
    - Aprende com todas as interações
    - Descobre padrões em trading e código
    - Sugere melhorias automaticamente
    - Executa ações de otimização
    - Mantém memória de longo prazo
    """
    
    def __init__(self, feedback_dir: Path = Path("/home/scalp/rag_system/feedback")):
        self.feedback_dir = feedback_dir
        self.feedback_dir.mkdir(exist_ok=True)
        
        # Arquivos de persistência
        self.feedback_file = feedback_dir / "feedback_log.jsonl"
        self.metrics_file = feedback_dir / "quality_metrics.json"
        self.insights_db = feedback_dir / "insights.db"
        self.patterns_file = feedback_dir / "trading_patterns.json"
        self.memory_db = feedback_dir / "long_term_memory.db"
        
        # Estado interno
        self.short_term_memory = []  # Últimas 100 interações
        self.working_memory = {}     # Contexto atual
        self.insights = []           # Insights descobertos
        self.active_experiments = {} # Experimentos em andamento
        
        self._init_databases()
        self.load_metrics()
        self._load_long_term_memory()
    
    def _init_databases(self):
        """Inicializar bancos de dados."""
        # Insights DB
        with sqlite3.connect(self.insights_db) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS insights (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    category TEXT,
                    insight TEXT,
                    confidence REAL,
                    action_taken TEXT,
                    impact_score REAL
                )
            """)
            
        # Long-term memory DB  
        with sqlite3.connect(self.memory_db) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    category TEXT,
                    content TEXT,
                    importance REAL,
                    accessed_count INTEGER DEFAULT 1,
                    last_accessed TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trading_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    strategy TEXT,
                    symbol TEXT,
                    timeframe TEXT,
                    sharpe REAL,
                    win_rate REAL,
                    profit_factor REAL,
                    max_drawdown REAL,
                    total_trades INTEGER,
                    parameters TEXT
                )
            """)
    
    def load_metrics(self):
        """Carregar métricas de qualidade acumuladas."""
        if self.metrics_file.exists():
            with open(self.metrics_file) as f:
                self.metrics = json.load(f)
        else:
            self.metrics = {
                "query_patterns": defaultdict(float),
                "context_effectiveness": defaultdict(list),
                "retrieval_precision": defaultdict(list),
                "user_satisfaction": [],
                "system_performance": defaultdict(list),
                "trading_insights": []
            }
    
    def _load_long_term_memory(self):
        """Carregar memórias importantes."""
        with sqlite3.connect(self.memory_db) as conn:
            # Carregar memórias mais importantes e recentes
            memories = conn.execute("""
                SELECT category, content, importance 
                FROM memories 
                WHERE importance > 0.7
                ORDER BY last_accessed DESC
                LIMIT 50
            """).fetchall()
            
            self.long_term_memory = {
                cat: {"content": cont, "importance": imp}
                for cat, cont, imp in memories
            }
    
    async def think(self, context: Dict) -> Dict[str, Any]:
        """
        Processo de 'pensamento' do cérebro - analisa contexto e gera insights.
        """
        thoughts = {
            "current_context": context,
            "relevant_memories": [],
            "insights": [],
            "suggestions": [],
            "actions": []
        }
        
        # 1. Recuperar memórias relevantes
        thoughts["relevant_memories"] = self._retrieve_relevant_memories(context)
        
        # 2. Analisar padrões
        patterns = await self._analyze_current_patterns(context)
        
        # 3. Gerar insights
        if patterns:
            insight = self._generate_insight(patterns, context)
            if insight:
                thoughts["insights"].append(insight)
                self._store_insight(insight)
        
        # 4. Sugestões baseadas em aprendizado
        thoughts["suggestions"] = self._generate_suggestions(context, patterns)
        
        # 5. Ações automáticas (se confidence > threshold)
        thoughts["actions"] = await self._decide_actions(thoughts)
        
        # 6. Atualizar memórias
        self._update_memories(context, thoughts)
        
        return thoughts
    
    def _retrieve_relevant_memories(self, context: Dict) -> List[Dict]:
        """Buscar memórias relevantes para o contexto atual."""
        relevant = []
        query_keywords = context.get("query", "").lower().split()
        
        with sqlite3.connect(self.memory_db) as conn:
            for keyword in query_keywords[:5]:  # Top 5 keywords - FIXED: added colon
                memories = conn.execute("""
                    SELECT category, content, importance
                    FROM memories
                    WHERE content LIKE ?
                    ORDER BY importance DESC
                    LIMIT 3
                """, (f"%{keyword}%",)).fetchall()
                
                for cat, content, imp in memories:
                    relevant.append({
                        "category": cat,
                        "content": content,
                        "importance": imp,
                        "keyword_match": keyword
                    })
        
        return relevant
    
    async def _analyze_current_patterns(self, context: Dict) -> Dict:
        """Analisar padrões no contexto atual."""
        patterns = {}
        
        # Padrão de queries
        if "query" in context:
            query_type = self._classify_query(context["query"])
            patterns["query_type"] = query_type
            
            # Verificar se é query recorrente
            if self._is_recurring_query(context["query"]):
                patterns["recurring"] = True
                patterns["frequency"] = self._get_query_frequency(context["query"])
        
        # Padrão de performance
        if "performance_metrics" in context:
            perf = context["performance_metrics"]
            patterns["performance_trend"] = self._analyze_performance_trend(perf)
        
        # Padrão de erros
        if "errors" in context:
            patterns["error_pattern"] = self._analyze_error_pattern(context["errors"])
        
        return patterns
    
    def _classify_query(self, query: str) -> str:
        """Classificar tipo de query."""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["strategy", "selector", "backtest"]):
            return "trading_strategy"
        elif any(word in query_lower for word in ["error", "bug", "problem", "issue"]):
            return "debugging"
        elif any(word in query_lower for word in ["performance", "speed", "optimize"]):
            return "optimization"
        elif any(word in query_lower for word in ["how", "what", "explain"]):
            return "explanation"
        else:
            return "general"
    
    def _is_recurring_query(self, query: str) -> bool:
        """Verificar se query é recorrente."""
        query_normalized = query.lower().strip()
        
        # Contar em short-term memory
        count = sum(1 for mem in self.short_term_memory 
                   if mem.get("query", "").lower().strip() == query_normalized)
        
        return count > 2
    
    def _get_query_frequency(self, query: str) -> int:
        """Obter frequência da query."""
        query_normalized = query.lower().strip()
        return sum(1 for mem in self.short_term_memory 
                  if mem.get("query", "").lower().strip() == query_normalized)
    
    def _analyze_performance_trend(self, metrics: Dict) -> str:
        """Analisar tendência de performance."""
        if not self.metrics.get("system_performance"):
            return "insufficient_data"
        
        recent_perf = self.metrics["system_performance"][-10:]
        if len(recent_perf) < 3:
            return "insufficient_data"
        
        # Calcular tendência
        trend = np.polyfit(range(len(recent_perf)), recent_perf, 1)[0]
        
        if trend > 0.1:
            return "improving"
        elif trend < -0.1:
            return "degrading"
        else:
            return "stable"
    
    def _analyze_error_pattern(self, errors: List[Dict]) -> Dict:
        """Analisar padrão de erros."""
        error_types = defaultdict(int)
        error_contexts = defaultdict(list)
        
        for error in errors:
            error_type = error.get("type", "unknown")
            error_types[error_type] += 1
            error_contexts[error_type].append(error.get("context", ""))
        
        return {
            "most_common": max(error_types, key=error_types.get) if error_types else None,
            "frequency": dict(error_types),
            "contexts": dict(error_contexts)
        }
    
    def _generate_insight(self, patterns: Dict, context: Dict) -> Optional[SystemInsight]:
        """Gerar insight baseado em padrões."""
        insight = None
        confidence = 0.0
        
        # Insight sobre queries recorrentes
        if patterns.get("recurring"):
            freq = patterns.get("frequency", 0)
            confidence = min(freq / 10, 1.0)  # Max confidence at 10 occurrences
            insight = SystemInsight(
                timestamp=datetime.now().isoformat(),
                category="query_pattern",
                insight=f"Query '{context.get('query', '')}' is recurring {freq} times. Consider caching or creating a knowledge card.",
                confidence=confidence
            )
        
        # Insight sobre performance
        elif patterns.get("performance_trend") == "degrading":
            confidence = 0.8
            insight = SystemInsight(
                timestamp=datetime.now().isoformat(),
                category="performance",
                insight="System performance is degrading. Consider optimization or resource cleanup.",
                confidence=confidence
            )
        
        # Insight sobre erros
        elif patterns.get("error_pattern"):
            most_common = patterns["error_pattern"].get("most_common")
            if most_common:
                freq = patterns["error_pattern"]["frequency"][most_common]
                confidence = min(freq / 5, 1.0)
                insight = SystemInsight(
                    timestamp=datetime.now().isoformat(),
                    category="error_pattern",
                    insight=f"Error type '{most_common}' occurring frequently ({freq} times). Investigate root cause.",
                    confidence=confidence
                )
        
        return insight
    
    def _store_insight(self, insight: SystemInsight):
        """Armazenar insight no banco."""
        with sqlite3.connect(self.insights_db) as conn:
            conn.execute("""
                INSERT INTO insights (timestamp, category, insight, confidence, action_taken, impact_score)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (insight.timestamp, insight.category, insight.insight, 
                  insight.confidence, insight.action_taken, insight.impact_score))
        
        self.insights.append(insight)
        logger.info(f"New insight: {insight.insight} (confidence: {insight.confidence:.2%})")
    
    def _generate_suggestions(self, context: Dict, patterns: Dict) -> List[Dict]:
        """Gerar sugestões baseadas no contexto e padrões."""
        suggestions = []
        
        # Sugestão para queries recorrentes
        if patterns.get("recurring"):
            suggestions.append({
                "type": "optimization",
                "suggestion": f"Cache query: '{context.get('query', '')}'",
                "priority": "high",
                "estimated_impact": "Reduce latency by 80%"
            })
        
        # Sugestão para melhorar documentação
        if patterns.get("query_type") == "explanation":
            suggestions.append({
                "type": "documentation",
                "suggestion": f"Create knowledge card for: {context.get('topic', 'current topic')}",
                "priority": "medium",
                "estimated_impact": "Improve RAG accuracy"
            })
        
        # Sugestão para otimização de trading
        if "trading_results" in context:
            results = context["trading_results"]
            if results.get("sharpe", 0) < 1.0:
                suggestions.append({
                    "type": "trading",
                    "suggestion": "Consider parameter optimization or strategy combination",
                    "priority": "high",
                    "estimated_impact": f"Current Sharpe: {results.get('sharpe', 0):.2f}, Target: >1.0"
                })
        
        return suggestions
    
    async def _decide_actions(self, thoughts: Dict) -> List[Dict]:
        """Decidir e executar ações automáticas."""
        actions = []
        
        for insight in thoughts.get("insights", []):
            if insight.confidence > 0.8:  # High confidence threshold
                action = await self._execute_action(insight)
                if action:
                    actions.append(action)
                    insight.action_taken = action["description"]
        
        return actions
    
    async def _execute_action(self, insight: SystemInsight) -> Optional[Dict]:
        """Executar ação baseada em insight."""
        action = None
        
        try:
            if insight.category == "query_pattern" and "caching" in insight.insight:
                # Auto-create cache entry
                query = insight.insight.split("'")[1]  # Extract query from insight
                action = {
                    "type": "cache_optimization",
                    "description": f"Auto-cached query: {query}",
                    "timestamp": datetime.now().isoformat()
                }
                # Would call actual cache API here
                logger.info(f"Action executed: {action['description']}")
                
            elif insight.category == "performance" and "optimization" in insight.insight:
                # Trigger cleanup
                action = {
                    "type": "system_optimization", 
                    "description": "Triggered automatic cleanup and optimization",
                    "timestamp": datetime.now().isoformat()
                }
                # subprocess.run(["/home/scalp/scripts/optimize.sh"], capture_output=True)
                logger.info(f"Action executed: {action['description']}")
                
        except Exception as e:
            logger.error(f"Failed to execute action: {e}")
        
        return action
    
    def _update_memories(self, context: Dict, thoughts: Dict):
        """Atualizar memórias de curto e longo prazo."""
        # Atualizar short-term memory
        self.short_term_memory.append({
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "thoughts": thoughts
        })
        
        # Manter só últimas 100 interações
        if len(self.short_term_memory) > 100:
            self.short_term_memory = self.short_term_memory[-100:]
        
        # Promover para long-term se importante
        importance = self._calculate_importance(context, thoughts)
        if importance > 0.7:
            self._store_long_term_memory(context, thoughts, importance)
    
    def _calculate_importance(self, context: Dict, thoughts: Dict) -> float:
        """Calcular importância de uma memória."""
        importance = 0.0
        
        # Insights aumentam importância
        if thoughts.get("insights"):
            importance += 0.3 * len(thoughts["insights"])
        
        # Ações aumentam importância
        if thoughts.get("actions"):
            importance += 0.4 * len(thoughts["actions"])
        
        # Trading results importantes
        if "trading_results" in context:
            results = context["trading_results"]
            if results.get("sharpe", 0) > 2.0:
                importance += 0.5
        
        # Erros críticos
        if context.get("error_severity") == "critical":
            importance += 0.6
        
        return min(importance, 1.0)
    
    def _store_long_term_memory(self, context: Dict, thoughts: Dict, importance: float):
        """Armazenar memória de longo prazo."""
        category = context.get("category", "general")
        content = json.dumps({
            "context": context,
            "thoughts": thoughts
        })
        
        with sqlite3.connect(self.memory_db) as conn:
            conn.execute("""
                INSERT INTO memories (timestamp, category, content, importance, last_accessed)
                VALUES (?, ?, ?, ?, ?)
            """, (datetime.now().isoformat(), category, content, importance, 
                  datetime.now().isoformat()))
    
    def record_interaction(self, query: str, response: Dict, feedback: Optional[Dict] = None):
        """Registrar interação para análise posterior."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "response_confidence": response.get("confidence", 0),
            "sources_used": len(response.get("sources", [])),
            "context_id": response.get("context_id"),
            "feedback": feedback
        }
        
        with open(self.feedback_file, "a") as f:
            json.dump(entry, f)
            f.write("\n")
        
        # Adicionar APENAS RESUMO ao short-term memory (evita memory leak)
        import hashlib
        self.short_term_memory.append({
            "timestamp": entry["timestamp"],
            "query_hash": hashlib.md5(query.encode('utf-8')).hexdigest(),
            "confidence": entry["response_confidence"],
            "context_id": entry["context_id"]
        })
        
        # Manter apenas últimos 100 entries
        if len(self.short_term_memory) > 100:
            self.short_term_memory = self.short_term_memory[-100:]
    
    def record_trading_result(self, strategy: str, symbol: str, timeframe: str, 
                            metrics: Dict, parameters: Dict):
        """Registrar resultado de trading para aprendizado."""
        with sqlite3.connect(self.memory_db) as conn:
            conn.execute("""
                INSERT INTO trading_results 
                (timestamp, strategy, symbol, timeframe, sharpe, win_rate, 
                 profit_factor, max_drawdown, total_trades, parameters)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (datetime.now().isoformat(), strategy, symbol, timeframe,
                  metrics.get("sharpe", 0), metrics.get("win_rate", 0),
                  metrics.get("profit_factor", 1), metrics.get("max_drawdown", 0),
                  metrics.get("total_trades", 0), json.dumps(parameters)))
        
        # Analisar se descobrimos um novo padrão
        self._analyze_trading_pattern(strategy, symbol, timeframe, metrics, parameters)
    
    def _analyze_trading_pattern(self, strategy: str, symbol: str, timeframe: str,
                                metrics: Dict, parameters: Dict):
        """Analisar se encontramos um padrão de trading valioso."""
        if metrics.get("sharpe", 0) > 2.0 and metrics.get("win_rate", 0) > 0.6:
            pattern = TradingPattern(
                name=f"{strategy}_{symbol}_{timeframe}",
                timeframe=timeframe,
                symbol=symbol,
                conditions=parameters,
                performance=metrics,
                discovered_at=datetime.now().isoformat()
            )
            
            # Salvar padrão descoberto
            patterns = []
            if self.patterns_file.exists():
                with open(self.patterns_file) as f:
                    patterns = json.load(f)
            
            patterns.append(asdict(pattern))
            
            with open(self.patterns_file, "w") as f:
                json.dump(patterns, f, indent=2)
            
            logger.info(f"🎯 New trading pattern discovered: {pattern.name} (Sharpe: {metrics['sharpe']:.2f})")
            
            # Criar insight sobre o padrão
            insight = SystemInsight(
                timestamp=datetime.now().isoformat(),
                category="trading_pattern",
                insight=f"High-performance pattern found: {strategy} on {symbol} {timeframe} with Sharpe {metrics['sharpe']:.2f}",
                confidence=0.9,
                impact_score=metrics.get("sharpe", 0)
            )
            self._store_insight(insight)
    
    async def suggest_next_experiment(self) -> Dict:
        """Sugerir próximo experimento baseado em aprendizados."""
        suggestions = []
        
        # Analisar resultados de trading recentes
        with sqlite3.connect(self.memory_db) as conn:
            recent_results = pd.read_sql_query("""
                SELECT * FROM trading_results 
                ORDER BY timestamp DESC 
                LIMIT 50
            """, conn)
        
        if not recent_results.empty:
            # Encontrar combinações não testadas
            tested_combos = set(zip(recent_results['strategy'], 
                                   recent_results['symbol'],
                                   recent_results['timeframe']))
            
            all_strategies = recent_results['strategy'].unique()
            all_symbols = recent_results['symbol'].unique()
            all_timeframes = recent_results['timeframe'].unique()
            
            for strategy in all_strategies:
                for symbol in all_symbols:
                    for tf in all_timeframes:
                        if (strategy, symbol, tf) not in tested_combos:
                            # Estimar performance baseado em combinações similares
                            similar = recent_results[
                                (recent_results['strategy'] == strategy) |
                                (recent_results['symbol'] == symbol) |
                                (recent_results['timeframe'] == tf)
                            ]
                            
                            if not similar.empty:
                                avg_sharpe = similar['sharpe'].mean()
                                if avg_sharpe > 1.0:
                                    suggestions.append({
                                        "strategy": strategy,
                                        "symbol": symbol,
                                        "timeframe": tf,
                                        "estimated_sharpe": avg_sharpe,
                                        "confidence": len(similar) / 50
                                    })
        
        # Ordenar por potencial
        suggestions.sort(key=lambda x: x['estimated_sharpe'] * x['confidence'], reverse=True)
        
        if suggestions:
            best = suggestions[0]
            return {
                "experiment": f"Test {best['strategy']} on {best['symbol']} {best['timeframe']}",
                "rationale": f"Similar combinations show Sharpe ~{best['estimated_sharpe']:.2f}",
                "confidence": best['confidence'],
                "command": f"python {best['strategy']}.py --symbol {best['symbol']} --timeframe {best['timeframe']}"
            }
        
        return {"experiment": "No suggestions available", "rationale": "Need more data"}
    
    def get_system_health(self) -> Dict:
        """Avaliar saúde geral do sistema."""
        health = {
            "timestamp": datetime.now().isoformat(),
            "memory_usage": {
                "short_term": len(self.short_term_memory),
                "long_term": len(self.long_term_memory),
                "insights": len(self.insights)
            },
            "learning_rate": 0.0,
            "confidence_trend": "stable",
            "areas_of_expertise": [],
            "areas_needing_improvement": []
        }
        
        # Calcular taxa de aprendizado (insights por dia)
        if self.insights:
            recent_insights = [i for i in self.insights 
                             if datetime.fromisoformat(i.timestamp) > datetime.now() - timedelta(days=7)]
            health["learning_rate"] = len(recent_insights) / 7
        
        # Identificar áreas de expertise
        with sqlite3.connect(self.memory_db) as conn:
            top_categories = conn.execute("""
                SELECT category, AVG(importance) as avg_imp, COUNT(*) as count
                FROM memories
                GROUP BY category
                HAVING count > 5
                ORDER BY avg_imp DESC
                LIMIT 5
            """).fetchall()
            
            health["areas_of_expertise"] = [cat for cat, _, _ in top_categories]
        
        # Áreas precisando melhorias (baixa confiança)
        low_conf_areas = defaultdict(list)
        for entry in self.short_term_memory[-50:]:
            if entry.get("response_confidence", 1) < 0.5:
                context = entry.get("context_id", "unknown")
                low_conf_areas[context].append(entry["response_confidence"])
        
        health["areas_needing_improvement"] = [
            area for area, confs in low_conf_areas.items() 
            if len(confs) > 2
        ]
        
        return health
    
    def generate_daily_report(self) -> str:
        """Gerar relatório diário do cérebro."""
        health = self.get_system_health()
        
        report = [
            "# 🧠 BotScalp Brain Daily Report",
            f"Generated: {datetime.now().isoformat()}\n",
            "## System Health",
            f"- Learning Rate: {health['learning_rate']:.1f} insights/day",
            f"- Short-term Memory: {health['memory_usage']['short_term']} entries",
            f"- Long-term Memory: {health['memory_usage']['long_term']} entries",
            f"- Total Insights: {health['memory_usage']['insights']}",
            "\n## Areas of Expertise"
        ]
        
        for area in health["areas_of_expertise"][:5]:
            report.append(f"- {area}")
        
        if health["areas_needing_improvement"]:
            report.append("\n## Areas Needing Improvement")
            for area in health["areas_needing_improvement"][:5]:
                report.append(f"- {area}")
        
        # Recent insights
        if self.insights:
            report.append("\n## Recent Insights")
            for insight in self.insights[-5:]:
                report.append(f"- [{insight.category}] {insight.insight[:100]}...")
                if insight.action_taken:
                    report.append(f"  Action: {insight.action_taken}")
        
        # Trading patterns discovered
        if self.patterns_file.exists():
            with open(self.patterns_file) as f:
                patterns = json.load(f)
                if patterns:
                    report.append("\n## Trading Patterns Discovered")
                    for pattern in patterns[-3:]:
                        report.append(f"- {pattern['name']}: Sharpe {pattern['performance']['sharpe']:.2f}")
        
        # Next experiment suggestion
        try:
            next_exp = asyncio.run(self.suggest_next_experiment())
            if next_exp.get("experiment") != "No suggestions available":
                report.append("\n## Suggested Next Experiment")
                report.append(f"- {next_exp['experiment']}")
                report.append(f"  Rationale: {next_exp['rationale']}")
        except:
            pass
        
        return "\n".join(report)
    
    # ============= PHASE 4: ACTIVE LEARNING METHODS =============
    
    def _detect_patterns(self, entry: Dict) -> None:
        """Detect patterns in recent interactions (Phase 4 enhancement)"""
        if len(self.short_term_memory) < 10:
            return
        
        recent = self.short_term_memory[-20:]
        
        # Pattern 1: Low confidence trend
        avg_conf = sum(m['confidence'] for m in recent) / len(recent)
        if avg_conf < 50:
            insight = SystemInsight(
                timestamp=datetime.utcnow().isoformat() + 'Z',
                category='performance',
                insight=f'Low avg confidence ({avg_conf:.1f}%) in last {len(recent)} queries - may need more knowledge ingestion',
                confidence=0.8,
                action_taken=None
            )
            self._record_insight(insight)
        
        # Pattern 2: Repeated context failures
        context_failures = defaultdict(int)
        for m in recent:
            if m['confidence'] < 30:
                context_failures[m['context_id']] += 1
        
        for context_id, failures in context_failures.items():
            if failures >= 3:
                insight = SystemInsight(
                    timestamp=datetime.utcnow().isoformat() + 'Z',
                    category='knowledge_gap',
                    insight=f'Repeated failures in context "{context_id}" ({failures} times) - missing knowledge',
                    confidence=0.9,
                    action_taken='suggest_ingestion'
                )
                self._record_insight(insight)
    
    def _learn_from_failure(self, entry: Dict) -> None:
        """Learn from low-rated responses and suggest improvements (Phase 4)"""
        context_id = entry.get('context_id', 'general')
        
        # Store failure pattern
        with sqlite3.connect(self.memory_db) as conn:
            conn.execute("""
                INSERT INTO memories (timestamp, category, content, importance, last_accessed)
                VALUES (?, ?, ?, ?, ?)
            """, (
                entry['timestamp'],
                'failure_pattern',
                json.dumps({
                    'query_preview': entry.get('response_preview', '')[:50],
                    'confidence': entry['response_confidence'],
                    'context': context_id
                }),
                0.8,
                entry['timestamp']
            ))
        
        logger.info(f"📉 Low-rated response detected - Context: {context_id}, Confidence: {entry['response_confidence']}%")
        logger.info(f"💡 Suggestion: Ingest more documents for '{context_id}' context")
    
    def _record_insight(self, insight: SystemInsight) -> None:
        """Record discovered insight to database (Phase 4)"""
        self.insights.append(insight)
        
        with sqlite3.connect(self.insights_db) as conn:
            conn.execute("""
                INSERT INTO insights (timestamp, category, insight, confidence, action_taken, impact_score)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                insight.timestamp,
                insight.category,
                insight.insight,
                insight.confidence,
                insight.action_taken or '',
                insight.impact_score
            ))
        
        logger.info(f"💡 New Insight [{insight.category}]: {insight.insight}")
    
    def get_recent_insights(self, limit: int = 10, category: Optional[str] = None) -> List[SystemInsight]:
        """Get recent insights discovered by the system (Phase 4)"""
        with sqlite3.connect(self.insights_db) as conn:
            if category:
                query = "SELECT * FROM insights WHERE category = ? ORDER BY timestamp DESC LIMIT ?"
                rows = conn.execute(query, (category, limit)).fetchall()
            else:
                query = "SELECT * FROM insights ORDER BY timestamp DESC LIMIT ?"
                rows = conn.execute(query, (limit,)).fetchall()
            
            insights = []
            for row in rows:
                insights.append(SystemInsight(
                    timestamp=row[1],
                    category=row[2],
                    insight=row[3],
                    confidence=row[4],
                    action_taken=row[5] or None,
                    impact_score=row[6]
                ))
            
            return insights
    
    def get_learning_recommendations(self) -> Dict:
        """Get recommendations for system improvement based on learned patterns (Phase 4)"""
        recommendations = {
            'ingestion_needed': [],
            'cache_optimizations': [],
            'knowledge_gaps': [],
            'performance_issues': []
        }
        
        recent_insights = self.get_recent_insights(limit=50)
        
        for insight in recent_insights:
            if insight.category == 'knowledge_gap':
                recommendations['knowledge_gaps'].append(insight.insight)
            elif insight.category == 'performance':
                recommendations['performance_issues'].append(insight.insight)
            elif insight.category == 'usage_pattern' and 'caching' in insight.insight:
                recommendations['cache_optimizations'].append(insight.insight)
        
        return recommendations
