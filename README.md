# ping4py

A Python wrapper/CLI tool for the `iputils-ping` tool.

## Install

To install this utility, just install it via pip. You can download the published wheels for each release and install those, or just install via git: `pip install git+https://github.com/ranleak/ping4py`.

## Restrictions

To send ICMP packets, a binary must open a raw socket. The Linux kernel restricts raw sockets to processes with root privileges or the `CAP_NET_RAW` capability. When standard package managers (`apt`, `pacman`) install `ping`, they automatically set file capabilities (`setcap cap_net_raw+ep`) or trigger the setuid bit. `pip` **does not preserve these specialized file permissions when extracting a wheel.** As a result, the binary bundled with the repo will throw an `Operation not permitted` error unless you run the CLI tool via `sudo`. If you are deploying this wrapper within a controlled environment (like a custom Docker container), this works great. In the near future, I will add a Snyk(.io) check so it's clear that this repo is safe to run via sudo. Until then, you can take my word for it!

## Development

### Compiling the Binary

By default, Linux distributions ship `ping` as part of the larger `iputils` suite, which includes tools like `arping` and `clockdiff`. For this project, you'll be compiling _only_ the `ping` utility into a standalone binary that can be bundled into Python wheels or custom environments.

1. **Install Build Dependencies**

   ```
   sudo apt-get update
   sudo apt-get install -y git meson ninja-build libcap-dev libidn2-dev
   ```

2. **Clone the Source**

   ```
   git clone --depth 1 https://github.com/iputils/iputils.git
   cd iputils
   ```

3. **Configure the Build Environment**

   ```
   meson setup builddir \
   -DBUILD_ARPING=false \
   -DBUILD_CLOCKDIFF=false \
   -DBUILD_TRACEPATH=false \
   -DBUILD_MANS=false \
   -DBUILD_HTML_MANS=false
   ```

4. **Compile the Binary**

   ```

   ninja -C builddir

   ```

The fresh, isolated binary is now compiled and located at `builddir/ping/ping`.

## Credits

- Contributors to the [iputils](https://github.com/iputils/iputils) project

  ![iputils Contributor Map](/readme-assets/iputils_contributors_small.png)

- [Rich](https://github.com/Textualize/rich) by [Textualize](https://www.textualize.io/) for our beautiful user interface

  ![rich Contributor Map](/readme-assets/rich_contributors_small.png)
