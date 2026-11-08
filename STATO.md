# Progetto video @leregoledelgentleman — stato (8 nov 2026)
In pausa. Funziona: GitHub Action monta immagini fisse (zoom) + voce edge-tts (it-IT-GiuseppeMultilingualNeural) + sottotitoli -> out/<nome>.mp4 (~74-93 s).
Job: jobs/<nome>.json con scene {image | image_prompt, text}. Ultimo video: out/ettore-90s-v3.mp4.
Pollinations (gratis): funziona ma a volte 402 (si riprova da sola), stile fotografico, scritta ritagliata. Gamma: stile fumetto coerente ma crediti finiti.
Problema aperto: volti incoerenti tra immagini diverse. Idea: scene senza volti (mani, dettagli, schiene) e uno stile unico, oppure generatore con immagine di riferimento (a pagamento).
Da fare: automazione quotidiana (task: scrive storia+job, poi pubblica Reel con Windsor create_video_post, URL raw GitHub).
