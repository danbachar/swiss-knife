#include <unistd.h>
#include <stdio.h>
#include <sys/socket.h>
#include <stdlib.h>
#include <netinet/in.h>
#include <string.h>
#include <net/if.h>
#include <sys/ioctl.h>
#include <errno.h>

#define BUFFSIZE 1024

int main(int argc, char const *argv[])
{
    struct sockaddr_in6 address;
    int server_socket, sock, addrlen = sizeof(address), on = 1, port = 64003;
    char *buffer = (char *)malloc(BUFFSIZE), *ok = "HTTP/1.1 200 OK\r\nContent-Length: 22\r\nContent-Type: text/html\r\n\r\nHello World from ATeam";
    // Use curl 169.254.68.39:8080
    uint32_t interfaceIndex = if_nametoindex("swissknife0");
    address.sin6_scope_id = interfaceIndex;

    if ((server_socket = socket(AF_INET6, SOCK_STREAM, 0)) == 0)
    {
        perror("socket failed");
        exit(EXIT_FAILURE);
    }
    if (setsockopt(server_socket, SOL_SOCKET, SO_REUSEADDR,
                   &on, sizeof(on)))
    {
        perror("setsockopt failed");
        exit(EXIT_FAILURE);
    }

    if (ioctl(server_socket, FIONBIO, (char *)&on) < 0)
    {
        perror("ioctl() failed");
        close(server_socket);
        exit(-1);
    }

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

    fd_set active_fd_set, read_fd_set;
    int ret;

    FD_ZERO (&active_fd_set);
    FD_SET (server_socket, &active_fd_set);

    while (1)
    {
        // reset read_fd_set every time
        read_fd_set = active_fd_set;

        // syscall select
        ret = select(FD_SETSIZE, &read_fd_set, NULL, NULL, NULL);
        if (ret < 0)
        {
            perror("select failed!\n");
            break;
        }
        else if (ret = 0)
        { //timeout, continue polling
            continue;
        }

        // check if any connection is active
        for (int i = 0; i < FD_SETSIZE; ++i)
            if (FD_ISSET (i, &read_fd_set))
            {
                if(i==server_socket){
                    while(1){//try to accept all incoming connections
                        if ((sock = accept(server_socket, (struct sockaddr *)&address, (socklen_t *)&addrlen)) < 0)
                        {
                            if (errno != EWOULDBLOCK)
                            {
                                perror("accept failed");
                                exit(EXIT_FAILURE);
                            }
                            break;
                        }
                        FD_SET (sock, &active_fd_set);
                    };
                }
                else
                {
                    /*Receive all incoming data on this socket before we loop back and call select again.*/
                    while(1){
                            
                        ret = recv(i, buffer, sizeof(char) * BUFFSIZE,0);
                        if (ret < 0)
                        {
                            if (errno != EWOULDBLOCK)
                            {
                                perror("  recv() failed");
                                close(i);
                                FD_CLR(i, &active_fd_set);
                            }
                            break;
                        }
                        if (ret == 0){
                            close(i);
                            FD_CLR(i, &active_fd_set);
                            break;
                        }
                        send(i, ok, strlen(ok), 0);
                    }
                }
            }
    }
    free(buffer);
    return EXIT_SUCCESS;
}
