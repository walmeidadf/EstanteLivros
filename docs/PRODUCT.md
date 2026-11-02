# Produto: Estante da Lila

## O que é
Uma estante pessoal, pública e instalável (PWA), com os ~300 livros lidos pela
Lila desde 2014, a partir de um caderno com 309 leituras numeradas.

## Pessoas
- **Lila**: leitora, não técnica, usa um Samsung Android. Prioridade: simplicidade.
- **Visitantes** (amigas, vindas do Instagram): só consultam.

## Decisões
- A estante é **pública** para leitura.
- **Só a Lila compartilha** (retrospectiva e cards). O botão de compartilhar só
  aparece no modo autenticado dela. Visitantes não veem esse botão.
- Resumos gerados por IA existem para **autoria (bio), ano e país**, e só aparecem
  com `approved: true`. **Não há sinopse de obra.**
- O cadastro de novas leituras (admin) fica para depois. Por enquanto, o catálogo é
  alterado em sessões de conversa com o Kiro.

## Princípios (do handoff de design)
- Simplicidade: poucos toques, sem login para visitantes, sem feed.
- Cara de estante de casa, não de dashboard.
- Mobile-first (390 px), funcionando bem no desktop.
- Português do Brasil em toda a interface.
- Só existe o **ano** de leitura. Nunca mostrar ou inventar dia e mês.
- Sem estrelas ou notas.
- Dados incompletos nunca parecem erro: usar os fallbacks do design.

## Referências
- [`design/DESIGN_HANDOFF.md`](../design/DESIGN_HANDOFF.md): regras visuais, componentes, telas, rotas, estados
- [`design/DESIGN_BRIEF.md`](../design/DESIGN_BRIEF.md): briefing original e dados
