Puntos a tener en cuenta al consumir o probar este modulo

1. en el endpoint de search_providers, el parametro que se monta en la url para realizar la bsuqueda es search, si no se monta asi, la peticion sera invalida y no devolvera nada

2.el proyecto en general usa los nombres de los endpoints, recordar siempre terminar la url con un hash/, si no saltara error, y los endpoints que reciben PK, la PK debe montarse en la url, en la posicion de antes del nombre del endpoint, es decir,  la ruta es: api/providers/{PK}/provider_by_nit
y los query params se montan despues de la llamada al endpoint y el ultimo hash /, es decir
api/providers/search_providers/?searc=query_param

sin mas observaciones todos los endpoints funcionan OK