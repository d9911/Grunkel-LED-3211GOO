# Grunkel LED-3211GOO

[English](README.md) · [Español](README.es.md) · [Русский](README.ru.md)

**1.0.0 · первая стабильная версия инструментария для проверенного Grunkel LED-3211GOO.** Браузер, Netflix, альтернатива YouTube, интернет-ТВ, трансляция с телефона, HDMI/AV и офлайн-фотозаставка с USB. Настраивается установленный Android; альтернативной прошивки здесь нет.

![Текущий Couchy HOME: прежние шесть приложений плюс HDMI и USB](assets/screenshots/couchy-satin-es.png)

[Прежний Projectivy home-es.png — оригинал сохранён](assets/screenshots/home-es.png). В публичной части оставлены только эти два снимка без ретуши и JPEG для обоев; происхождение: [assets/showcase.json](assets/showcase.json).

## Выбери одно из трёх меню

Это три альтернативных лаунчера, а не разные модели телевизора. Два меню многоязычные; настройки Plume 1.3 только английские. Закреплены проверенные версии и SHA-256 в [apps.lock.json](apps.lock.json).

| Меню | Языки настроек | Обои/темы | Нюанс | Официальный релиз / APK |
| --- | --- | --- | --- | --- |
| Couchy 1.0.6 · основной | RU / ES / EN¹ | Свой JPEG бесплатно; светлая/тёмная тема не подтверждена | Dock с восемью карточками; импорт/экспорт JSON | [Release](https://github.com/conreo/couchy-launcher/releases/tag/v1.0.6) · [APK](https://github.com/conreo/couchy-launcher/releases/download/v1.0.6/Couchy-Launcher-v1.0.6.apk) |
| Projectivy 4.72 | RU / ES / EN проверены | Свои обои/темы в этой версии требуют Premium | Прежняя строка входов; сохранён как альтернатива | [Release](https://github.com/spocky/miproja1/releases/tag/4.72) · [APK](https://github.com/spocky/miproja1/releases/download/4.72/ProjectivyLauncher-4.72-c97-xda-release.apk) |
| Plume 1.3 | Настройки только EN | Свой JPEG и Light / Dark / Auto бесплатно | Подходит, если английские настройки устраивают | [Release](https://github.com/aradhyas8/Plume_Launcher/releases/tag/v1.3) · [APK](https://github.com/aradhyas8/Plume_Launcher/releases/download/v1.3/Plume-1.3.apk) |

¹ В Couchy 1.0.6 русский/испанский есть в списке языка, отдельного English нет. Английский проверен через язык приложения Android и JSON `"language": "en"`; подробнее ниже. Наличие переводов не означает проверки каждой фразы. На 21.10.2026 официальные ссылки latest ведут на эти три закреплённые версии; автоматических обновлений не выполнялось.

<a id="tv-specifications"></a>

## Характеристики телевизора

Данные сняты **21.10.2026** с одного экземпляра. Источники и точные вычисления: [hardware.json](hardware.json). Доступная RAM/память — датированный снимок; размер снимка/режим Android не доказывает физическое разрешение матрицы.

| Характеристика                      | Проверенное значение                                       | Источник                 |
| ----------------------------------- | ---------------------------------------------------------- | ------------------------ |
| Модель / экран                      | Grunkel LED-3211GOO · LED-телевизор 32 дюйма               | [label](hardware.json)   |
| Питание                             | 100–240 В AC · 50/60 Гц                                    | [label](hardware.json)   |
| Потребление по шильдику / выход USB | 56 Вт · USB 5 В / 0,5 А                                    | [label](hardware.json)   |
| Название Android / производитель    | Grunkel 2K Android TV · Expressluck                        | [getprop](hardware.json) |
| Плата / платформа                   | `martin` / MediaTek `mt5867`                               | [getprop](hardware.json) |
| Логические процессоры               | 4 записи: `0`, `1`, `2`, `3`                               | [cpuinfo](hardware.json) |
| Операционная система                | Android 14 · API 34 · указанный системой патч `2026-06-01` | [getprop](hardware.json) |
| ABI приложений Android              | 32-битный Android · `armeabi-v7a`, `armeabi`               | [getprop](hardware.json) |
| RAM, доступная ядру                 | 935352 KiB ≈ 913,43 MiB (`935352 / 1024`)                  | [meminfo](hardware.json) |
| Раздел пользовательских данных | 4205976 KiB ≈ 4.011 ГиБ (`KiB / 1048576`) | [runtime-storage](hardware.json) |
| Доступное место, снимок | 2550860 KiB ≈ 2.433 ГиБ · 60.65% | [runtime-storage](hardware.json) |
| Доступная RAM, снимок | 240228 KiB ≈ 234.60 МиБ (`KiB / 1024`) | [runtime-storage](hardware.json) |
| Объём swap | 716796 KiB ≈ 700.00 МиБ; это не физическая RAM | [runtime-storage](hardware.json) |
| Политика частот CPU | Доступно 0,75–1,50 ГГц; текущий предел 1,45 ГГц; не изменялся | [cpu-frequency](hardware.json) |
| Внутренний режим дисплея Android | 1280 × 720, около 60 Гц; спецификация матрицы не подтверждена | [display-runtime](hardware.json) |
| Заводской режим low-RAM | `ro.config.low_ram=true` | [properties-runtime](hardware.json) |
| Часовой пояс интерфейса | Европейский часовой пояс; сохраняется настройка ТВ | [properties-runtime](hardware.json) |
| Размер снимка интерфейса            | 1280 × 720 px; не характеристика матрицы                   | [capture](hardware.json) |
| Состояние загрузки                  | Загрузчик `locked` · verified boot `green`                 | [getprop](hardware.json) |

<a id="compatibility"></a>

## Совместимость

Expressluck / `martin` / MediaTek `mt5867`, Android 14 / API 34. Точный fingerprint закреплён в [профиле](profiles/martin-mt5867-android14.json); `doctor` отказывается работать с другой платой/сборкой. Не изменяй проверку ради принудительной установки. Совпадение названия модели не доказывает совместимость.

Это проверенная конфигурация одного ТВ. Сохранность после сброса, испанский после сброса, полное воспроизведение Netflix и весь 30-минутный цикл не подтверждены: [verification.json](verification.json).

<a id="technology-stack"></a>

## Технологии

Python **3.9+** со стандартной библиотекой, GNU Make и официальный Google ADB. Авторские Android-приложения — обычная Java с закреплёнными локальными JDK/Android-инструментами. Node/npm необязательны; npm-зависимостей нет. Автоматическая подготовка Android-инструментов закреплена для **macOS arm64**; другим системам нужен совместимый ручной toolchain (`--toolchain`). Полный цикл проверен только на macOS.

[ADB](https://developer.android.com/tools/adb) · [версии инструментов](android/photos/toolchain.lock.json) · [разработчикам](CONTRIBUTING.md).

<a id="configured-applications"></a>

## Установленные приложения

| Компонент | Версия / назначение |
| --- | --- |
| Одно выбранное меню | Couchy 1.0.6, Projectivy 4.72 или Plume 1.3 |
| SmartTube F-Droid | 32.56 / 2446; публичное YouTube-видео воспроизводилось без Google-аккаунта |
| OpenTV | 0.11.7; разрешённые интернет-каналы M3U |
| AirPlay Server | 0.0.36; приём изображения с iPhone |
| TV Bro | 2.1.6; WebView-браузер для пульта |
| Netflix / Live TV | Заводские приложения сохранены; Netflix требует свой аккаунт |
| Grunkel Photos | Авторское 0.2.0; необязательные офлайн USB-фото и заставка |
| Карточки HDMI + USB | Авторские 0.1.0; необязательные офлайн-ярлыки без разрешений |
| Material Files | Необязательный 1.7.5 для выбора JPEG/JSON в Couchy на этой прошивке |

База: **одно меню + четыре общих приложения**, а не все три меню. Фотозаставка и карточки HDMI/USB собираются отдельно. Официальные APK-ссылки, версии и хеши: [apps.lock.json](apps.lock.json).

<a id="quick-start"></a>

## Быстрый старт: инициализация одного меню

На ТВ включи параметры разработчика/отладку USB, подтверди ключ только своего компьютера и узнай точный ADB serial/адрес. USB-отладка не делает любой USB-разъём сервисным: не используй произвольный USB-A–USB-A кабель. Для беспроводного сопряжения — [инструкция ADB](https://developer.android.com/tools/adb).

Команды выполняются из проекта. **Везде замени `TV_ADDRESS:5555`** на свой разрешённый адрес ADB либо точный USB serial. Python 3 и Make должны быть установлены. Выбери **один блок**; между `menu` и `configure` заверши приветствие пультом.

### Couchy: несколько языков и бесплатные обои

```sh
make install TV=TV_ADDRESS:5555 LAUNCHER=couchy
make menu TV=TV_ADDRESS:5555 LAUNCHER=couchy
# Заверши приветствие Couchy на телевизоре.
make configure TV=TV_ADDRESS:5555 LAUNCHER=couchy
```

### Projectivy: несколько языков; свои обои требуют Premium

```sh
make install TV=TV_ADDRESS:5555 LAUNCHER=projectivy
make menu TV=TV_ADDRESS:5555 LAUNCHER=projectivy
# Заверши приветствие Projectivy на телевизоре.
make configure TV=TV_ADDRESS:5555 LAUNCHER=projectivy
```

### Plume: английские настройки; обои/светлая/тёмная темы бесплатно

```sh
make install TV=TV_ADDRESS:5555 LAUNCHER=plume
make menu TV=TV_ADDRESS:5555 LAUNCHER=plume
# Заверши приветствие Plume на телевизоре.
make configure TV=TV_ADDRESS:5555 LAUNCHER=plume
```

`install` подготовит официальный ADB, подключится, проверит устройство и SHA-256 скачанных/установленных APK. `configure` применит обратимый профиль, AirPlay/HOME, выключит запросы установки APK, проверит результат и откроет меню. При ошибке шаги останавливаются; порядок сохраняется с `make -j`.

На подготовленном ТВ доступен `make setup TV=TV_ADDRESS:5555 LAUNCHER=couchy`. Он не завершает приветствие и не импортирует личную раскладку, плейлисты или папку фото. Адрес можно сохранить частно: скопируй [device.example.json](device.example.json) в `device.local.json`. Поиск устройств по сети не выполняется. `make plan` только читает состояние.

<a id="menu-languages-and-clock"></a>

## Меню, языки и часы

Основное меню — **Couchy**: Netflix, AirPlay, Live TV, OpenTV, SmartTube, TV Bro, HDMI и USB в одном Dock-ряду. В настройках экрана выбери размер значков **XS**. Часы в 24-часовом формате сохраняют текущий европейский часовой пояс; язык Android и Couchy сейчас испанский.

Для замены только меню на подготовленном ТВ подставь `couchy`, `projectivy` или `plume`:

```sh
make launcher-list
make launcher-install TV=TV_ADDRESS:5555 LAUNCHER=plume
make menu TV=TV_ADDRESS:5555 LAUNCHER=plume
# До назначения HOME заверши приветствие.
make launcher-use TV=TV_ADDRESS:5555 LAUNCHER=plume
make verify TV=TV_ADDRESS:5555
```

Установка/просмотр не меняют HOME. Успешный `launcher-use` сохраняет выбор по serial/fingerprint в частном `launcher.local.json`. Приоритет: `--launcher` → `GRUNKEL_LAUNCHER`/Make `LAUNCHER` → сохранённый выбор → Couchy из профиля. Журнал отката содержит прежние HOME и локальный выбор.

**Языки:** Android сохраняет RU/ES/EN. Переводы Projectivy проверены. Настройки Plume 1.3 английские. В списке языков Couchy есть русский/испанский; английский работает через язык приложения Android или штатный импорт JSON с `"language": "en"`. После языковых проб «Системный по умолчанию» оставлял русскую дату/интерфейс; явный выбор Español исправил это. После смены языка проверь дату и настройки.

**Обои:** [satin-teal-copper.jpg](img/satin-teal-copper.jpg) — статичный JPEG во внутренней памяти, от USB не зависит. В Couchy выбери его через фото-селектор; видеообои выключены. Встроенный селектор — заглушка, поэтому использован необязательный Material Files: команды Python `download-apps files` / `install files`, затем `make files-access-status`. `make files-access-on` — только при разрешённом владельцем доступе к общим файлам ТВ/накопителей: он допускает также изменение/удаление. `files-access-off` отключает доступ, прежний режим сохранён в журнале. Папки ноутбука по сети не подключаются. Полные команды: [техническая справка](docs/technical-reference.md).

<a id="internet-tv-and-casting"></a>

## Интернет-ТВ и трансляция

В OpenTV: Add source → Enter on TV instead → URL M3U. Проверен `https://www.tdtchannels.com/lists/tv.m3u8` от [TDTChannels](https://www.tdtchannels.com/listas/), воспроизводился La 1. Источник преимущественно испанский; полного набора RU/EN нет. Добавляй только разрешённые тебе плейлисты.

iPhone в той же сети → Пункт управления → Повтор экрана → Grunkel → PIN на ТВ. Владелец подтвердил изображение; AirPlay настроен на 720p/30fps. С Redmi 15C работала **трансляция YouTube**, полный повтор Android-экрана не подтверждён. Google Cast/Play Services сохранены. Netflix с DRM смотри в родном приложении; воспроизведение Netflix не проверялось. SmartTube проигрывал публичное видео без Google-аккаунта.

<a id="tv-and-inputs"></a>

## USB-файлы, фотографии и входы

Добавление двух авторских карточек и необязательной фотозаставки:

```sh
make shortcuts-install TV=TV_ADDRESS:5555
make photos-install TV=TV_ADDRESS:5555
make shortcuts-status TV=TV_ADDRESS:5555
make photos-choose TV=TV_ADDRESS:5555
# Пульт: стрелки + OK для выбора флешки/папки, BACK назад.
make photos-apply TV=TV_ADDRESS:5555
make photos-status TV=TV_ADDRESS:5555
```

**HDMI:** реальные HDMI 1–3 и AV; выбранный источник открывается заводским приложением ТВ. Выбор HDMI 1 подтверждён активной сессией входа; новое внешнее изображение остальных входов не проверялось. Кнопка INPUT/SOURCE и `make inputs` остаются. Поиск/удаление каналов не запускается.

**USB:** штатный просмотр файлов и прежний выбор папки фотографий. Без смонтированной флешки кнопки внутри страницы серые/выключены; сама карточка HOME остаётся видимой. Физическое извлечение/возврат проверены: страница обновлялась автоматически, прежняя папка снова стала доступна. Ярлыки не запрашивают разрешений, не запускают службы и не записывают файлы USB.

**Фотопоказ:** 5 минут простоя → 25 минут фото → сон на 30-й минуте; смена каждые **30 секунд**. Выбери папку с фотографиями непосредственно внутри. Стрелки/OK/BACK — навигация; в предпросмотре ←/→ — фото, OK — пауза, BACK — выход. Ошибки декодирования пропускаются; проверены JPEG/PNG. До 1000 файлов-кандидатов, декодирование до 1280×720. Ручной предпросмотр удерживает экран включённым и не равен автоматическому циклу. Полный цикл/сохранность после перезагрузки не проверены; активные HDMI/медиа могут удерживать ТВ включённым. Для обновлений сохраняй ключ подписи фотоприложения.

<a id="project-structure"></a>

## Структура проекта

Для быстрого входа: [AGENTS.md](AGENTS.md) — текущее состояние/ограничения, [verification.json](verification.json) — проверки с датой. [CONTRIBUTING.md](CONTRIBUTING.md) — проверка проекта/обновление закреплённых версий; [CHANGELOG.md](CHANGELOG.md) — состав 1.0.0.

```text
README{,.es,.ru}.md       инструкции и инициализация трёх меню
docs/technical-reference.md  подробные команды/удалённый доступ
hardware.json            характеристики с источниками
verification.json        проверенное состояние и ограничения
apps.lock.json           официальные APK, версии и SHA-256
profiles/                точная сборка и обратимый профиль
scripts/                 ADB CLI, сборка, офлайн-проверка и экспорт
android/photos/          авторская USB-фотозаставка
android/shortcuts/        авторские HDMI/USB-карточки EN/ES/RU
assets/screenshots/       текущий Couchy и старый home-es.png
img/                     повторно используемый JPEG
```

Инструменты, APK, частные снимки/логи/ключи, `*.local.json`, backups и exports игнорируются. Публикуй только проверенный набор; экспортёр использует явный белый список файлов/хешей.

<a id="privacy-and-performance"></a>

## Приватность и производительность

Профиль отключает 13 проверенных необязательных пакетов, укорачивает анимации, сохраняет Cast, DRM, WebView, службы ТВ/входов и обновления. Он не удаляет APK из прошивки и не увеличивает RAM. В ненужных приложениях по выбору владельца очищался только кэш; удаление приложений/обновлений в setup не входит.

**Полное отсутствие телеметрии и постоянное ускорение не доказаны.** Vendor ACR оставался запущен; потоковые приложения обращаются к своим серверам. Приватный браузер не означает анонимность. Громкость при проверках не повышать выше ограничения владельца **1/100**, использовать mute.

Запросы установки APK выключены у установленных Projectivy, Plume, TV Bro и Material Files. `make installer-on` разрешает только необязательный Projectivy; после установки нужен `make installer-off`. Штатный установщик/ADB сохранены. Доступ к файлам и разрешение установки APK — разные настройки.

<a id="recovery-and-maintenance"></a>

## Восстановление и обслуживание

```sh
make check                         # Офлайн: исходники/документация/JSON/XML/экспорт.
make verify TV=TV_ADDRESS:5555      # Только чтение профиля/HOME/закреплённых APK.
make storage TV=TV_ADDRESS:5555     # RAM и раздел данных, без очистки.
make rollback TV=TV_ADDRESS:5555 JOURNAL=backups/FOLDER/changes.json
make stock-home TV=TV_ADDRESS:5555 # Штатное HOME; данные приложений сохраняются.
make export OUTPUT=exports/NEW_NAME.zip
```

Перед повторным применением изучи отклонения. Ранее `com.cltv.fast` и настройка отчётов об ошибках возвращались, причина не установлена. Журналы должны принадлежать тому же ТВ; откатывай в обратном порядке. Они не удаляют новые приложения и не отменяют все ручные настройки. Заводской сброс удалит пользовательскую конфигурацию; ядро/разделы и испанский по умолчанию после сброса не изменялись.

Couchy сохранял `Download/CouchyBackup.json`; импорт через Material Files проверен. JSON держи приватным (содержит список пакетов), исходный JPEG — отдельно. Резервы Plume с APK/состоянием не являются копией закрытых данных или образом прошивки.

Управление мышью/клавиатурой ноутбука подтверждено в HID-режиме: необязательные `make screen-bootstrap`, затем `make screen`; звук/синхронизация буфера выключены. SSH, физические устройства и границы восстановления — в [технической справке](docs/technical-reference.md). Подготовка этой версии не меняет настройки ТВ. Git-коммиты/публикация выполняются владельцем вручную: [CONTRIBUTING.md](CONTRIBUTING.md).

<a id="author"></a>

## Автор

[Denis Gutsuliak (d9911.org)](https://t.me/d9911/) · [admin@d9911.org](mailto:admin@d9911.org). Данные автора: [package.json](package.json).

<a id="license"></a>

## Лицензия

[GPL-3.0-or-later](LICENSE) для авторского инструментария; см. [NOTICE](NOTICE). Сторонние приложения, прошивка, инструменты, интерфейсы/значки и товарные знаки сохраняют права своих владельцев. APK, ключи, аккаунты и личные медиа не распространяются.
