3drepacker
---
Набор скриптов для перепаковки 3d blu-ray образов

Для работы, вы должны установить зависимости через:
```
uv install
```

Распаковать файлы `eac3to` и `FRIM в соответствующие папки

Ориентир

- В папке eac3to должен находится `eac3to.exe`
- В папке FRIM должен находиться `FRIMDecode64.exe`

И запустить
```
uv run main.py
```

```
usage: main.py [-h] -d DRIVE [-crf CRF] [-t THREADS] [-su | --skip-unpack | --no-skip-unpack] [-rac | --reencode-audio-channel | --no-reencode-audio-channel] [-uhac | --use-hardware-acceleration | --no-use-hardware-acceleration]
```