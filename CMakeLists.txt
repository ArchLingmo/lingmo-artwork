cmake_minimum_required(VERSION 3.16)
project(lingmo-artwork NONE)

# Images are committed as-is (the generate*.py ones are reproducible), so building needs no Python
install(FILES wallpapers/lingmo-arch-monterey-4k.png
              wallpapers/archlingmo-light.jpg wallpapers/archlingmo-dark.jpg
              wallpapers/archmac-light.jpg wallpapers/archmac-dark.jpg
        DESTINATION ${CMAKE_INSTALL_PREFIX}/share/backgrounds/lingmoos)
