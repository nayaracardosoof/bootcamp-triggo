import gradio as gr

from research_report_agent.config import AUTO_MODE, DEPTHS, GAIA_API_BASE_URL, MODES
from research_report_agent.gaia import run_gaia_benchmark
from research_report_agent.service import run_research

EXAMPLES = [
    [
        "Compare smolagents, LangChain e CrewAI para criar um agente pesquisador simples.",
        AUTO_MODE,
        "Média",
        True,
        True,
        False,
    ],
    [
        "Pesquise sobre galinhas.",
        AUTO_MODE,
        "Média",
        True,
        True,
        False,
    ],
    [
        "Como publicar um app Gradio no Hugging Face Spaces?",
        AUTO_MODE,
        "Média",
        True,
        False,
        False,
    ],
    [
        "Crie uma skill para code review em projetos Python.",
        AUTO_MODE,
        "Alta",
        True,
        True,
        True,
    ],
]

with gr.Blocks(title="Research Report Agent") as demo:
    gr.Markdown(
        """
# Research Report Agent

Agente pesquisador com `smolagents` que busca informações na web, pode inferir automaticamente o formato de saída e gera artefatos validados:

- relatórios de pesquisa em Markdown;
- skills reutilizáveis em Markdown com manifest JSON de carregamento;
- modo GAIA para benchmark/submissão no avaliador da Hugging Face.

Opcionalmente, o agente também avalia o artefato gerado com um evaluation prompt.
        """.strip()
    )

    with gr.Tabs():
        with gr.Tab("Pesquisa / Skill"):
            with gr.Row():
                with gr.Column(scale=2):
                    question_input = gr.Textbox(
                        label="Pergunta, tema da pesquisa ou skill desejada",
                        placeholder="Ex: Crie uma skill sobre como construir agentes pesquisadores com smolagents.",
                        lines=4,
                    )
                    with gr.Row():
                        mode_input = gr.Dropdown(
                            choices=list(MODES.keys()),
                            value=AUTO_MODE,
                            label="Modo",
                        )
                        depth_input = gr.Dropdown(
                            choices=list(DEPTHS.keys()),
                            value="Média",
                            label="Profundidade",
                        )
                    gr.Markdown(
                        "No modo **Automático**, o app usa regras simples para escolher entre relatório, resumo, comparação, plano de ação ou skill."
                    )
                    with gr.Row():
                        sources_input = gr.Checkbox(value=True, label="Incluir fontes/referências")
                        evaluate_input = gr.Checkbox(value=True, label="Avaliar artefato")
                        export_input = gr.Checkbox(value=False, label="Exportar arquivo(s)")
                    submit_button = gr.Button("Executar pesquisa", variant="primary")

                with gr.Column(scale=3):
                    artifact_output = gr.Markdown(label="Relatório ou skill")
                    evaluation_output = gr.Markdown(label="Avaliação")
                    file_output = gr.File(label="Arquivo(s) exportado(s)")

            gr.Examples(
                examples=EXAMPLES,
                inputs=[
                    question_input,
                    mode_input,
                    depth_input,
                    sources_input,
                    evaluate_input,
                    export_input,
                ],
            )

            submit_button.click(
                fn=run_research,
                inputs=[
                    question_input,
                    mode_input,
                    depth_input,
                    sources_input,
                    export_input,
                    evaluate_input,
                ],
                outputs=[artifact_output, evaluation_output, file_output],
            )

        with gr.Tab("GAIA / Hugging Face"):
            gr.Markdown(
                """
## Modo GAIA

Busca tarefas no endpoint do avaliador, resolve cada pergunta com o agente, faz retry automático quando a validação detectar resposta ruim, revisa o formato final, valida o payload e salva os arquivos em `gaia_runs/`.

Use **Enviar para avaliador remoto** somente quando `username` e `agent_code` estiverem corretos.
                """.strip()
            )
            with gr.Row():
                with gr.Column(scale=2):
                    gaia_username = gr.Textbox(label="Hugging Face username", placeholder="seu-usuario")
                    gaia_agent_code = gr.Textbox(
                        label="Agent code / Space / repositório",
                        placeholder="https://huggingface.co/spaces/seu-usuario/seu-space",
                    )
                    gaia_api_url = gr.Textbox(label="GAIA API base URL", value=GAIA_API_BASE_URL)
                    gaia_max_tasks = gr.Number(label="Máximo de tarefas (0 = todas)", value=0, precision=0)
                    gaia_submit = gr.Checkbox(value=False, label="Enviar para avaliador remoto")
                    gaia_run_button = gr.Button("Executar GAIA", variant="primary")

                with gr.Column(scale=3):
                    gaia_report_output = gr.Markdown(label="Relatório GAIA")
                    gaia_files_output = gr.File(label="Arquivos GAIA exportados")

            def _run_gaia_from_ui(username, agent_code, api_url, max_tasks, submit):
                max_tasks_int = int(max_tasks or 0)
                return run_gaia_benchmark(
                    username=username or "",
                    agent_code=agent_code or "",
                    max_tasks=max_tasks_int if max_tasks_int > 0 else None,
                    submit=bool(submit),
                    api_base_url=api_url or GAIA_API_BASE_URL,
                    save_outputs=True,
                )

            gaia_run_button.click(
                fn=_run_gaia_from_ui,
                inputs=[gaia_username, gaia_agent_code, gaia_api_url, gaia_max_tasks, gaia_submit],
                outputs=[gaia_report_output, gaia_files_output],
            )

if __name__ == "__main__":
    demo.launch()
 