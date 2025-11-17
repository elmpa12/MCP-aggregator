#!/usr/bin/env python3
"""
CLI for RAG system
"""

import sys
from pathlib import Path
import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.advanced_rag import AdvancedRAGSystem

console = Console()

@click.group()
def cli():
    """Advanced RAG CLI - Intelligent question answering system"""
    pass

@cli.command()
@click.argument('query', required=True)
@click.option('--code/--no-code', default=True, help='Include code search')
@click.option('--format', type=click.Choice(['text', 'markdown', 'json']), default='markdown')
def ask(query: str, code: bool, format: str):
    """
    Ask a question to the RAG system
    
    Example:
        rag ask "Como funciona o selector21?"
        rag ask "Explique a arquitetura do sistema" --format json
    """
    console.print("[blue]🤖 Processando sua pergunta...[/blue]\n")
    
    try:
        rag = AdvancedRAGSystem()
        result = rag.query(query, include_code=code)
        
        if format == 'json':
            import json
            console.print_json(json.dumps({
                "answer": result.answer,
                "confidence": result.confidence,
                "num_docs": result.num_docs_used,
                "time_ms": result.query_time_ms
            }, indent=2))
        elif format == 'markdown':
            console.print(Panel(
                Markdown(result.answer),
                title=f"[green]Resposta (confiança: {result.confidence:.0%})[/green]",
                border_style="green"
            ))
            console.print(f"\n[dim]📊 {result.num_docs_retrieved} docs recuperados, {result.num_docs_used} usados | ⏱️  {result.query_time_ms:.0f}ms[/dim]")
        else:
            console.print(result.answer)
            console.print(f"\nConfiança: {result.confidence:.0%}")
        
    except Exception as e:
        console.print(f"[red]❌ Erro: {e}[/red]")
        sys.exit(1)

@cli.command()
def test():
    """Run test query"""
    console.print("[blue]🧪 Executando teste...[/blue]\n")
    
    try:
        rag = AdvancedRAGSystem()
        result = rag.query("Como funciona o sistema de memória?")
        
        console.print(Panel(
            Markdown(result.answer),
            title="[green]Resultado do Teste[/green]",
            border_style="green"
        ))
        console.print(f"\n[green]✅ Teste concluído com sucesso![/green]")
        console.print(f"Confiança: {result.confidence:.0%} | Tempo: {result.query_time_ms:.0f}ms")
    except Exception as e:
        console.print(f"[red]❌ Teste falhou: {e}[/red]")
        sys.exit(1)

@cli.command()
def server():
    """Start API server"""
    console.print("[blue]🚀 Iniciando API server...[/blue]")
    console.print("[dim]Pressione Ctrl+C para parar[/dim]\n")
    
    import uvicorn
    from api.server import app
    
    uvicorn.run(app, host="0.0.0.0", port=8765)


if __name__ == '__main__':
    cli()
