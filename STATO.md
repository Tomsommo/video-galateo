# Progetto video @leregoledelgentleman — stato (10 nov 2026)
13 nov: a Tommaso NON piacciono silhouette e immagini Pollinations; gli piace la PRIMA versione (5 immagini Gamma a fumetti, a colori, volti coerenti). v6 = stesse 5 immagini + inquadrature diverse ("crop": [x,y,lato]) per avere ~23 scene.
(Ettore cappotto marrone, Leonardo abito blu e orologio d'oro, Matteo giacca bianca, direttore frac nero), stesso stile e stesso seed per tutte le immagini.
Ritmo: un'immagine ogni 3-4 secondi (~26 scene per 90 s), pausa breve tra scene ("pad").
Funziona: GitHub Action monta immagini fisse (zoom) + voce edge-tts (it-IT-GiuseppeMultilingualNeural) + sottotitoli -> out/<nome>.mp4.
Job: jobs/<nome>.json con "style" (davanti a ogni prompt), "pad", scene {image | image_prompt, seed, text}. Ultimo: jobs/ettore-90s-v5.json (v4: 103 s, volti ancora visibili nei primi piani di mani -> v5 solo silhouette controluce o oggetti senza persone).
Pollinations (gratis): a volte 402, ora 6 tentativi con 15 s di pausa.
Scelta immagini: previews/<nome>.json -> preview.py crea 3 varianti per scena e le tavole previews/<nome>-tavola-N.jpg; Tommaso sceglie (es. 1B 2A ...), poi job video con "image": "previews/<nome>/sNN_x.jpg".
Da fare: musica di sottofondo senza diritti; automazione quotidiana (task: scrive storia+job, poi pubblica Reel con Windsor create_video_post, URL raw GitHub).
