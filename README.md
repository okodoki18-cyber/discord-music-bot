# discord-music-bot

Discord için basit bir müzik botu. YouTube araması/URL ile şarkı oynatır ve kuyruk yönetimi yapar.

## Özellikler
- `!play <şarkı veya url>` ile müzik ekleme
- Otomatik kuyruk oynatma
- `!skip`, `!stop`, `!pause`, `!resume`
- `!queue`, `!np`
- `!join`, `!leave`

## Kurulum
1. Python 3.10+ kurun.
2. FFmpeg kurulu olduğundan emin olun (`ffmpeg` komutu çalışmalı).
3. Bağımlılıkları yükleyin:
   ```bash
   pip install -r requirements.txt
   ```
4. `.env.example` dosyasını `.env` olarak kopyalayıp token girin.

## Çalıştırma
```bash
python main.py
```

## Komutlar
- `!join`
- `!play never gonna give you up`
- `!play https://www.youtube.com/watch?v=dQw4w9WgXcQ`
- `!queue`
- `!skip`
- `!stop`
- `!pause`
- `!resume`
- `!np`
- `!leave`
