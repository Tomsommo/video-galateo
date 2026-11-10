# Progetto video @leregoledelgentleman — stato (10 nov 2026)
Ripreso il 10 nov. Scelta: solo strumenti gratuiti, scene SENZA VOLTI (mani, dettagli, persone di spalle), personaggi riconoscibili dagli abiti
(Ettore cappotto marrone, Leonardo abito blu e orologio d'oro, Matteo giacca bianca, direttore frac nero), stesso stile e stesso seed per tutte le immagini.
Ritmo: un'immagine ogni 3-4 secondi (~26 scene per 90 s), pausa breve tra scene ("pad").
Funziona: GitHub Action monta immagini fisse (zoom) + voce edge-tts (it-IT-GiuseppeMultilingualNeural) + sottotitoli -> out/<nome>.mp4.
Job: jobs/<nome>.json con "style" (davanti a ogni prompt), "pad", scene {image | image_prompt, seed, text}. Ultimo: jobs/ettore-90s-v4.json.
Pollinations (gratis): a volte 402, ora 6 tentativi con 15 s di pausa.
Da fare: musica di sottofondo senza diritti; automazione quotidiana (task: scrive storia+job, poi pubblica Reel con Windsor create_video_post, URL raw GitHub).
