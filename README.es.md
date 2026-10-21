# Grunkel LED-3211GOO

[English](README.md) · [Español](README.es.md) · [Русский](README.ru.md)

**1.0.0 · primera versión estable del kit para el Grunkel LED-3211GOO probado.** Navegador, Netflix, alternativa a YouTube, canales de internet, emisión desde el móvil, HDMI/AV y salvapantallas USB sin conexión. Configura Android instalado; no es un firmware alternativo.

![Couchy HOME actual: seis aplicaciones originales más HDMI y USB](assets/screenshots/couchy-satin-es.png)

[Projectivy anterior home-es.png — original conservado](assets/screenshots/home-es.png). Sólo estas dos capturas sin retoques y el JPEG reutilizable se incluyen públicamente; procedencia: [assets/showcase.json](assets/showcase.json).

## Elige uno de tres launchers

Son tres menús de inicio alternativos, no modelos distintos de TV. Dos tienen ajustes multilingües; Plume 1.3 sólo tiene ajustes en inglés. Versiones probadas y SHA-256: [apps.lock.json](apps.lock.json).

| Launcher | Idiomas de ajustes | Fondo/temas | Detalle | Lanzamiento oficial / APK |
| --- | --- | --- | --- | --- |
| Couchy 1.0.6 · predeterminado | RU / ES / EN¹ | JPEG propio gratis; cambio claro/oscuro sin verificar | Dock de ocho tarjetas; importar/exportar JSON | [Release](https://github.com/conreo/couchy-launcher/releases/tag/v1.0.6) · [APK](https://github.com/conreo/couchy-launcher/releases/download/v1.0.6/Couchy-Launcher-v1.0.6.apk) |
| Projectivy 4.72 | RU / ES / EN comprobados | JPEG/temas propios requirieron Premium en esta versión | Fila anterior de entradas; alternativa conservada | [Release](https://github.com/spocky/miproja1/releases/tag/4.72) · [APK](https://github.com/spocky/miproja1/releases/download/4.72/ProjectivyLauncher-4.72-c97-xda-release.apk) |
| Plume 1.3 | Ajustes sólo EN | JPEG propio y Light / Dark / Auto gratis | Alternativa si se aceptan ajustes en inglés | [Release](https://github.com/aradhyas8/Plume_Launcher/releases/tag/v1.3) · [APK](https://github.com/aradhyas8/Plume_Launcher/releases/download/v1.3/Plume-1.3.apk) |

¹ Couchy 1.0.6 incluye ruso/español en el selector, pero no una opción English. Se comprobó inglés con el idioma nativo por aplicación y JSON `"language": "en"`; detalles abajo. No se auditó cada traducción. El 2026-10-21 los enlaces oficiales latest seguían apuntando a estas tres versiones fijadas; sin actualizaciones automáticas.

<a id="tv-specifications"></a>

## Especificaciones del televisor

Hechos observados en una unidad el **2026-10-21**. Fuentes y cálculos exactos: [hardware.json](hardware.json). RAM/espacio libres son una instantánea fechada; captura/modo Android no demuestran resolución física del panel.

| Característica                | Valor comprobado                                   | Fuente                   |
| ----------------------------- | -------------------------------------------------- | ------------------------ |
| Modelo / pantalla             | Grunkel LED-3211GOO · televisor LED de 32 pulgadas | [label](hardware.json)   |
| Alimentación                  | 100–240 V AC · 50/60 Hz                            | [label](hardware.json)   |
| Consumo nominal / salida USB  | 56 W según etiqueta · USB 5 V / 0,5 A              | [label](hardware.json)   |
| Modelo Android / fabricante   | Grunkel 2K Android TV · Expressluck                | [getprop](hardware.json) |
| Placa / plataforma            | `martin` / MediaTek `mt5867`                       | [getprop](hardware.json) |
| Procesadores lógicos          | 4 entradas: `0`, `1`, `2`, `3`                     | [cpuinfo](hardware.json) |
| Sistema operativo             | Android 14 · API 34 · parche indicado `2026-06-01` | [getprop](hardware.json) |
| ABI de aplicaciones Android   | Android de 32 bits · `armeabi-v7a`, `armeabi`      | [getprop](hardware.json) |
| RAM indicada por el kernel    | 935352 KiB ≈ 913,43 MiB (`935352 / 1024`)          | [meminfo](hardware.json) |
| Partición de datos | 4205976 KiB ≈ 4.011 GiB (`KiB / 1048576`) | [runtime-storage](hardware.json) |
| Espacio disponible, captura | 2550860 KiB ≈ 2.433 GiB · 60.65% | [runtime-storage](hardware.json) |
| RAM disponible, captura | 240228 KiB ≈ 234.60 MiB (`KiB / 1024`) | [runtime-storage](hardware.json) |
| Capacidad swap | 716796 KiB ≈ 700.00 MiB; no es RAM física | [runtime-storage](hardware.json) |
| Política de frecuencias CPU | 0,75–1,50 GHz disponibles; límite actual 1,45 GHz; sin cambios | [cpu-frequency](hardware.json) |
| Modo de pantalla interna Android | 1280 × 720, aproximadamente 60 Hz; panel no verificado | [display-runtime](hardware.json) |
| Indicador low-RAM de fábrica | `ro.config.low_ram=true` | [properties-runtime](hardware.json) |
| Idioma / zona horaria actual | `es-ES` / `Europe/Madrid`; idioma tras restablecer sin verificar | [properties-runtime](hardware.json) |
| Tamaño de captura de interfaz | 1280 × 720 px; no especifica el panel              | [capture](hardware.json) |
| Estado de arranque            | Cargador `locked` · verified boot `green`          | [getprop](hardware.json) |

<a id="compatibility"></a>

## Compatibilidad

Expressluck / `martin` / MediaTek `mt5867`, Android 14 / API 34. Huella exacta fijada en [el perfil](profiles/martin-mt5867-android14.json); `doctor` rechaza otra placa/compilación. No cambies la protección para forzar instalación. Mismo nombre comercial no demuestra compatibilidad.

Configuración comprobada en una unidad, no ROM universal. No están demostrados persistencia tras restablecimiento, español de fábrica, reproducción completa de Netflix ni ciclo completo de 30 minutos: [verification.json](verification.json).

<a id="technology-stack"></a>

## Tecnologías

Python **3.9+** estándar, GNU Make y Google ADB oficial. Aplicaciones propias en Java con JDK/Android fijados. Node/npm es opcional, sin dependencias npm. La preparación automática de herramientas Android está fijada para **macOS arm64**; otros sistemas requieren toolchain manual compatible (`--toolchain`). Sólo macOS se ejercitó de extremo a extremo.

[ADB](https://developer.android.com/tools/adb) · [herramientas fijadas](android/photos/toolchain.lock.json) · [contribuir](CONTRIBUTING.md).

<a id="configured-applications"></a>

## Aplicaciones configuradas

| Componente | Versión / función |
| --- | --- |
| Un launcher | Couchy 1.0.6, Projectivy 4.72 o Plume 1.3 |
| SmartTube F-Droid | 32.56 / 2446; vídeo público reproducido sin cuenta Google |
| OpenTV | 0.11.7; canales autorizados M3U |
| AirPlay Server | 0.0.36; receptor de imagen iPhone |
| TV Bro | 2.1.6; navegador WebView con mando |
| Netflix / Live TV | Aplicaciones de fábrica conservadas; Netflix requiere cuenta propia |
| Grunkel Photos | Original 0.2.0; fotos/salvapantallas USB opcional sin conexión |
| Tarjetas HDMI + USB | Originales 0.1.0; accesos opcionales sin permisos |
| Material Files | Opcional 1.7.5 para elegir JPEG/JSON de Couchy en este firmware |

Base: **un launcher + cuatro aplicaciones comunes**, no los tres launchers. Fotos y HDMI/USB se compilan aparte. Enlaces oficiales APK, versiones y hashes: [apps.lock.json](apps.lock.json).

<a id="quick-start"></a>

## Inicio rápido: inicializar un launcher

Activa desarrollo/depuración USB, autoriza sólo la clave de tu ordenador y averigua el serial/dirección ADB exacto. Depuración USB no convierte cualquier conector en puerto de servicio; no uses un cable USB-A–USB-A cualquiera. Para emparejar por Wi-Fi sigue [ADB oficial](https://developer.android.com/tools/adb).

Ejecuta desde el proyecto. **Sustituye `TV_ADDRESS:5555` en todas las órdenes** por tu ADB autorizado o serial USB exacto. Requiere Python 3 y Make. Elige **un solo bloque**; termina la bienvenida con el mando entre `menu` y `configure`.

### Couchy: varios idiomas y fondo gratis

```sh
make install TV=TV_ADDRESS:5555 LAUNCHER=couchy
make menu TV=TV_ADDRESS:5555 LAUNCHER=couchy
# Termina la bienvenida de Couchy en el TV.
make configure TV=TV_ADDRESS:5555 LAUNCHER=couchy
```

### Projectivy: varios idiomas; fondo propio requiere Premium

```sh
make install TV=TV_ADDRESS:5555 LAUNCHER=projectivy
make menu TV=TV_ADDRESS:5555 LAUNCHER=projectivy
# Termina la bienvenida de Projectivy en el TV.
make configure TV=TV_ADDRESS:5555 LAUNCHER=projectivy
```

### Plume: ajustes en inglés; fondo/claro/oscuro gratis

```sh
make install TV=TV_ADDRESS:5555 LAUNCHER=plume
make menu TV=TV_ADDRESS:5555 LAUNCHER=plume
# Termina la bienvenida de Plume en el TV.
make configure TV=TV_ADDRESS:5555 LAUNCHER=plume
```

`install` prepara ADB oficial, conecta, protege la identidad y verifica SHA-256 descargados/instalados. `configure` aplica perfil reversible, AirPlay/HOME y solicitudes APK desactivadas, verifica y abre el menú. Se detiene al fallar y mantiene orden con `make -j`.

Para un TV preparado: `make setup TV=TV_ADDRESS:5555 LAUNCHER=couchy`. No completa bienvenida ni importa diseño, listas o carpeta personal. Guarda dirección opcionalmente copiando [device.example.json](device.example.json) a `device.local.json`. No se explora la red; `make plan` sólo lee.

<a id="menu-languages-and-clock"></a>

## Menú, idiomas y reloj

HOME actual: **Couchy**, con Netflix, AirPlay, Live TV, OpenTV, SmartTube, TV Bro, HDMI y USB en una fila Dock. Elige iconos **XS** en Pantalla para ver las ocho tarjetas. Reloj de 24h, zona retenida Europe/Madrid; Android y Couchy en español.

Para cambiar sólo launcher en un TV preparado, sustituye `couchy`, `projectivy` o `plume`:

```sh
make launcher-list
make launcher-install TV=TV_ADDRESS:5555 LAUNCHER=plume
make menu TV=TV_ADDRESS:5555 LAUNCHER=plume
# Termina la bienvenida antes de seleccionar HOME.
make launcher-use TV=TV_ADDRESS:5555 LAUNCHER=plume
make verify TV=TV_ADDRESS:5555
```

Instalar/probar no cambia HOME. `launcher-use` guarda la elección por serial/huella en `launcher.local.json` privado. Prioridad: `--launcher` → `GRUNKEL_LAUNCHER`/Make `LAUNCHER` → elección guardada → Couchy del perfil. El diario conserva HOME y elección local originales.

**Idiomas:** Android conserva RU/ES/EN. Se comprobaron tres traducciones Projectivy; Plume 1.3 sólo tiene ajustes ingleses. En Couchy el selector ofrece ruso/español; inglés funciona mediante idioma nativo por aplicación o importando JSON `"language": "en"`. Tras pruebas, Predeterminado del sistema dejó fecha/interfaz rusas; elegir Español explícitamente lo corrigió. Comprueba fecha y ajustes después de cambiar idioma.

**Fondo:** [satin-teal-copper.jpg](img/satin-teal-copper.jpg) es un JPEG interno, sin depender del USB. Elígelo en el selector de fotos Couchy; vídeo/aéreos desactivados. El selector original es vacío, por eso se usó Material Files opcional. Instala con Python `download-apps files` / `install files`, revisa `make files-access-status` y usa `make files-access-on` sólo con autorización para almacenamiento compartido/conectado: permite también modificar/borrar. `files-access-off` revoca; modo original en diario. No se conectan carpetas del portátil. Órdenes completas: [referencia técnica](docs/technical-reference.md).

<a id="internet-tv-and-casting"></a>

## TV por internet y emisión

En OpenTV: Add source → Enter on TV instead → URL M3U. Fuente probada: `https://www.tdtchannels.com/lists/tv.m3u8` de [TDTChannels](https://www.tdtchannels.com/listas/); La 1 se reprodujo. Es principalmente española; no hay oferta completa RU/EN configurada. Usa listas autorizadas.

iPhone en la misma LAN → Centro de control → Duplicar pantalla → Grunkel → PIN del TV. El propietario confirmó imagen; AirPlay a 720p/30fps. Funcionó **YouTube Cast** desde Redmi 15C; duplicación completa de Android no demostrada. Google Cast/Play Services conservados. Para Netflix DRM usa la aplicación nativa; reproducción Netflix no verificada. SmartTube reprodujo vídeo público sin cuenta Google.

<a id="tv-and-inputs"></a>

## Archivos USB, fotos y entradas

Añade las dos tarjetas originales y fotos opcionales:

```sh
make shortcuts-install TV=TV_ADDRESS:5555
make photos-install TV=TV_ADDRESS:5555
make shortcuts-status TV=TV_ADDRESS:5555
make photos-choose TV=TV_ADDRESS:5555
# Mando: flechas + OK eligen USB/carpeta; BACK vuelve.
make photos-apply TV=TV_ADDRESS:5555
make photos-status TV=TV_ADDRESS:5555
```

**HDMI:** entradas registradas HDMI 1–3 y AV; abre el TV de fábrica. Selección HDMI 1 comprobada por sesión activa; las otras imágenes externas no se probaron de nuevo. INPUT/SOURCE y `make inputs` siguen disponibles. Sin búsqueda/borrado de canales.

**USB:** explorador nativo y selector existente de fotos. Sin unidad montada, botones de la página grises/desactivados; tarjeta HOME permanece visible. Extracción/reinserción física comprobada: página actualizada automáticamente y carpeta anterior disponible otra vez. Los accesos no piden permisos, ejecutan servicios ni escriben en USB.

**Fotos:** 5 minutos inactivo → 25 minutos fotos → reposo al minuto 30; cambio cada **30 segundos**. Elige carpeta con imágenes directas. Flechas/OK/BACK navegan; vista previa ←/→ cambia, OK pausa, BACK sale. Se omiten errores de decodificación; JPEG/PNG comprobados. Hasta 1000 candidatos, decodificación hasta 1280×720. Vista previa manual mantiene despierto y no es el ciclo automático. Ciclo completo/persistencia tras reinicio no comprobados; HDMI/media activos pueden mantener despierto. Conserva claves de firma para actualizaciones.

<a id="project-structure"></a>

## Estructura del proyecto

Entrada rápida: [AGENTS.md](AGENTS.md) — estado actual/reglas; [verification.json](verification.json) — pruebas fechadas. [CONTRIBUTING.md](CONTRIBUTING.md) — validación/actualización de versiones; [CHANGELOG.md](CHANGELOG.md) — contenido 1.0.0.

```text
README{,.es,.ru}.md       guías e inicialización de tres launchers
docs/technical-reference.md  órdenes avanzadas/remoto
hardware.json            hechos con fuentes
verification.json        estado comprobado y límites
apps.lock.json           APK oficiales, versiones y SHA-256
profiles/                compilación exacta y perfil reversible
scripts/                 ADB CLI, builds, validación y export
android/photos/          fotos USB originales sin conexión
android/shortcuts/        tarjetas HDMI/USB EN/ES/RU
assets/screenshots/       Couchy actual y antiguo home-es.png
img/                     JPEG estático reutilizable
```

Herramientas, APK, capturas/logs/claves privadas, `*.local.json`, backups y exports se ignoran. No publiques todo el directorio; el exportador usa lista explícita de archivos/hashes.

<a id="privacy-and-performance"></a>

## Privacidad y rendimiento

El perfil desactiva 13 paquetes opcionales revisados, acorta animaciones y conserva Cast, DRM, WebView, servicios TV/entradas y actualizaciones. No borra APK de firmware ni aumenta RAM. Sólo se limpió caché de aplicaciones opcionales por petición del propietario; setup no desinstala aplicaciones/actualizaciones.

**Ausencia total de telemetría y mejora permanente no demostradas.** ACR del fabricante seguía activo; aplicaciones contactan proveedores. Incógnito no implica anonimato. No subas volumen sobre **1/100** del propietario; usa silencio en pruebas.

Solicitudes APK desactivadas en Projectivy, Plume, TV Bro y Material Files instalados. `make installer-on` permite sólo Projectivy opcional; después usa `make installer-off`. Instalador del sistema/ADB conservados. Acceso a archivos e instalación APK son controles distintos.

<a id="recovery-and-maintenance"></a>

## Recuperación y mantenimiento

```sh
make check                         # Offline: código/docs/JSON/XML/export.
make verify TV=TV_ADDRESS:5555      # Sólo lectura de perfil/HOME/APK fijados.
make storage TV=TV_ADDRESS:5555     # RAM/datos fechados; sin limpiar.
make rollback TV=TV_ADDRESS:5555 JOURNAL=backups/FOLDER/changes.json
make stock-home TV=TV_ADDRESS:5555 # HOME de fábrica, datos conservados.
make export OUTPUT=exports/NEW_NAME.zip
```

Revisa diferencias antes de reaplicar. `com.cltv.fast` y reporte de errores volvieron en pruebas anteriores; causa desconocida. Diarios sólo del mismo TV y en orden inverso; no desinstalan nuevos APK ni revierten toda elección manual. Restablecer fábrica elimina configuración de usuario; no se modificaron kernel/particiones ni español predeterminado tras reset.

Couchy guardó `Download/CouchyBackup.json`; carga por Material Files comprobada. Mantén JSON privado (inventario de paquetes) y JPEG aparte. Reservas APK/estado de Plume no son datos privados completos ni firmware.

Ratón/teclado del portátil confirmados por HID: opcionales `make screen-bootstrap`, después `make screen`; audio/sincronización de portapapeles desactivados. SSH, periféricos físicos y recuperación: [referencia técnica](docs/technical-reference.md). Esta preparación no cambia ajustes TV. Commits/publicación Git manuales por el propietario: [CONTRIBUTING.md](CONTRIBUTING.md).

<a id="author"></a>

## Autor

[Denis Gutsuliak (d9911.org)](https://t.me/d9911/) · [admin@d9911.org](mailto:admin@d9911.org). Metadatos: [package.json](package.json).

<a id="license"></a>

## Licencia

[GPL-3.0-or-later](LICENSE) para el kit original; [NOTICE](NOTICE). Aplicaciones de terceros, firmware, herramientas, interfaces/iconos y marcas conservan sus derechos. No se distribuyen APK, claves, cuentas ni medios privados.
