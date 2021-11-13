#include <unistd.h>
#include <stdio.h>
#include <sys/socket.h>
#include <stdlib.h>
#include <netinet/in.h>
#include <string.h>

int main(int argc, char const *argv[])
{
    struct sockaddr_in address;
    int server_socket, sock, addrlen = sizeof(address), reuse = 1, port = 8080;
    char *buffer = malloc(1024), *ok = "HTTP/1.1 200 OK\n";
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(port);

    if ((server_socket = socket(AF_INET, SOCK_STREAM, 0)) == 0)
    {
        perror("socket failed");
        exit(EXIT_FAILURE);
    }
    if (setsockopt(server_socket, SOL_SOCKET, SO_REUSEADDR,
                   &reuse, sizeof(reuse)))
    {
        perror("setsockopt failed");
        exit(EXIT_FAILURE);
    }
    if (bind(server_socket, (struct sockaddr *)&address,
             addrlen) < 0)
    {
        perror("bind failed");
        exit(EXIT_FAILURE);
    }
    if (listen(server_socket, 3) < 0)
    {
        perror("listen failed");
        exit(EXIT_FAILURE);
    }
    while (1)
    {
        memset(buffer, 0, sizeof(&buffer));
        if ((sock = accept(server_socket, (struct sockaddr *)&address,
                           (socklen_t *)&addrlen)) < 0)
        {
            perror("accept");
            exit(EXIT_FAILURE);
        }
        read(sock, buffer, sizeof(&buffer));
        printf("received: \n%s\n", buffer);
        send(sock, ok, strlen(ok), 0);
        printf("sent: \n%s\n", ok);
        close(sock);
    }
    free(buffer);
    return EXIT_SUCCESS;
}