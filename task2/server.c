#include <unistd.h>
#include <stdio.h>
#include <sys/socket.h>
#include <stdlib.h>
#include <netinet/in.h>
#include <string.h>
#include <net/if.h>
#define BUFFSIZE 1024

int main(int argc, char const *argv[])
{
    struct sockaddr_in6 address;
    int server_socket, sock, addrlen = sizeof(address), reuse = 1, port = 64000;
    char *buffer = (char *)malloc(BUFFSIZE), *ok = "HTTP/1.1 200 OK\r\nContent-Length: 22\r\nContent-Type: text/html\r\n\r\nHello World from ATeam";
    uint32_t interfaceIndex;

    if ((server_socket = socket(AF_INET6, SOCK_STREAM, 0)) == 0)
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
    interfaceIndex = if_nametoindex("swissknife0");
    address.sin6_scope_id = interfaceIndex;
    address.sin6_family = AF_INET6;
    address.sin6_addr = in6addr_any;
    address.sin6_port = htons(port);
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
        memset(buffer, 0, sizeof(char) * BUFFSIZE);
        if ((sock = accept(server_socket, (struct sockaddr *)&address,
                           (socklen_t *)&addrlen)) < 0)
        {
            perror("accept");
            exit(EXIT_FAILURE);
        }
        while (1)
        { //serve the client until the client close the connection
            int n = read(sock, buffer, sizeof(char) * BUFFSIZE);
            if (n <= 0)
            {
                close(sock);
                break;
            }
            else
            {
                send(sock, ok, strlen(ok), 0);
            }
        }
    }
    free(buffer);
    return EXIT_SUCCESS;
}
