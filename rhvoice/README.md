This is a web service based on flask and speech synthesizer [RHVoice](https://github.com/Olga-Yakovleva/RHVoice). Thanks to the REST API, it is easy to integrate as a TTS provider.

##Docker
### Via docker_starter script
Run\upgrade from hub: `./rhvoice_rest.py --upgrade`

Full description [here](https://github.com/Aculeasis/docker-starter)

### Ready dockers
- aarch64 `docker run -d -p 8080:8080 aculeasis/rhvoice-rest:arm64v8`
- armv7l `docker run -d -p 8080:8080 aculeasis/rhvoice-rest:arm32v7`
- x86_64 `docker run -d -p 8080:8080 aculeasis/rhvoice-rest:amd64`

### Building and running docker
    git clone https://github.com/RazeVSergey/FreePBX
    cd rhvoice-rest
    # Specify a Dockerfile for the target architecture
    docker build -t rhvoice-rest -f Dockerfile.arm64v8 .
    docker run -d -p 8080:8080 rhvoice-rest

## API
    http://server/say?
    text=<text>
    &voice=<
             aleksandr|anna|arina|artemiy|elena|irina|pavel| # Russian
             alan|bdl|clb|slt| # English
             spomenka| # Esperanto
             natia| #Georgian
             azamat|nazgul| # Kyrgyz
             talgat| #Tatar
             anatol|natalia| #Ukrainian
             kiko| # Macedonian
             leticia-f123 # Portuguese
             >
    & format=<wav|mp3|opus|flac>
    &rate=0..100
    & pitch=0..100
    & volume=0..100
`SERVER` - Address and port of rhvoice-rest. The default install to localhost will be `localhost:8080`.
Of course, you can install the rhvoice-rest server on one machine and the client on another. Especially true for weak single-payers.

`text` - URL-encoded string. Required parameter.

`voice` - Voice from RHVoice [full list](https://github.com/Olga-Yakovleva/RHVoice/wiki/Latest-version-%28Russian%29).
`anna` is used by default and as an alternate speaker.

`format` - The format of the returned file. The default is `mp3`.

`rate` - Rate of speech. The default is `50`.

`pitch` - The pitch of the voice. The default is `50`.

`volume` - The volume of the voice. The default is `50`.

## Native launch
First you need to install the dependencies:

`pip3 install flask pymorphy2 rhvoice-wrapper`

Build and install [RHVoice](https://github.com/Olga-Yakovleva/RHVoice) or install [rhvoice-wrapper-bin](https://github.com/Aculeasis/rhvoice-wrapper-bin) providing libraries and RHVoice data. The second option is recommended for Windows. does not require assembly.

And put `rhvoice_tools` next to app.py - renaming `preprocessing` from [RHVoice-dictionary/tools](https://github.com/vantu5z/RHVoice-dictionary/tree/master/tools).

To support `mp3`, `opus` and `flac` you need to install `lame`, `opus-tools` and `flac`

### Script installation on debian-based distributions as a service
    git clone https://github.com/RazeVSergey/FreePBX
    cd rhvoice
    chmod +x install.sh
    sudo ./install.sh
Service status `sudo systemctl status rhvoice-rest.service`

### Windows startup features
You need to set the path through environment variables. If you are using `rhvoice-wrapper-bin` then the first 2 do not need to be set:

**RHVOICELIBPATH** to `RHVoice.dll` of the same architecture as python and **RHVOICEDATAPATH** to the folder with languages â€â€and voices. By default they are placed in `C:\Program Files (x86)\RHVoice\data`

Optional: **LAMEPATH**, **OPUSENCPATH** and **FLACPATH** to support appropriate formats.

Tested on Windows 10 and Python 3.6.

## Settings
All settings are set through environment variables, before running the script or when creating a docker container (via `-e`):
- **RHVOICELIBPATH**: Path to the RHVoice library. The default is `RHVoice.dll` on Windows and `libRHVoice.so` on Linux.
- **RHVOICEDATAPATH**: Path to RHVoice data. Default is `/usr/local/share/RHVoice`.
- **THREADED**: The number of synthesis processes running, determines the number of requests that can be processed at the same time. If `> 1` the generators will be run as separate processes, which will significantly increase memory consumption. The recommended maximum value is `1.5 * core count`. The default is `1`.
- **LAMEPATH**: Path to `lame` or `lame.exe`, if file not found `mp3` support will be disabled. The default is `lame`.
- **OPUSENCPATH**: Path to `opusenc` or `opusenc.exe`, if file not found `opus` support will be disabled. The default is `opusenc`.
- **FLACPATH**: Path to `flac` or `flac.exe`, if file not found `flac` support will be disabled. The default is `flac`.
- **RHVOICE_DYNCACHE**: If set and not equal to `no`, `disable` or `false` caches the query result for the duration of the query. Enabled automatically with **RHVOICE_FCACHE**.
- **RHVOICE_FCACHE**: If set and not equal to `no`, `disable` or `false` file cache will be enabled. Reading from the cache almost does not increase the response speed, but significantly reduces the load time of all data. May not work properly on Windows. The cache is disabled by default.
- **RHVOICE_FCACHE_LIFETIME**: If the cache is enabled, sets the lifetime of cache files in hours, calculated from time