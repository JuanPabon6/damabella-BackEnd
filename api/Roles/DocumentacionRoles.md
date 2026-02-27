Puntos a tener en cuenta al consumir o probar los endpoints

1. En los Metodos: POST, PUT Y DELETE, hay que colocar un hash(/), si no se coloca el hash la peticion devolvera status Error 500 internal server error

2. En el metodo Get: search_params, el parametro que se monta en la url para hacer la busqueda es: search, es decir el name del input debe ser search, si no se realiza esta accion, la peticion no montara los query_params en la url, por lo tanto no realizara la busqueda

3. Este modulo tiene multiples modelos creados, asi mismo los permisos son manejados directamente desde este modulo, ya que las viewsets y las urls estan declaradas dentro de esta app, solamente es montar en la url 

No hay mas observaciones por hacer en este modulo, todo funciona OK, listo para consumir