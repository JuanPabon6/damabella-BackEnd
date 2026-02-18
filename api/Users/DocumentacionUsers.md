Puntos a tener en cuenta al consumir o probar este modulo

1. La contraseña es de caracter write_only, es decir, no se vera en ninguna peticion get, posteriormente sera hasheada y guardada

2. El metodo delete se maneja pasando el documento de identidad, el cual es la Primary Key del modelo, pasando otro argumento no se generara la eliminacion

3. El buscador de este modulo se maneja unica y exclusivamente con llave (search), si no se coloca search en la url, el query_param no recibira bien el request y devolvera null

4. En el cambio de estado, en el request body, hay que enviar unicamente el campo is_activive, que es el que maneja el estado verdadero o falso, si se envia algo mas en el payload la peticion fallara y no realizara ningun cambio

no hay mas observaciones en este modulo, todo esta ok