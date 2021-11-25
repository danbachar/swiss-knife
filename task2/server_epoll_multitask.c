/*
 *  This version of epoll takes advantages of SO_REUSEPORT (since Linux 3.9) mechanism
 *  to handle with thundering herd problem in multitasks/multithreads system. 
 *  Like Nginx, there are WORKER_NUM subprocesses which bind to to the same port.
 *  As they are different epollfds, there is no need to add mutex lock. The kernel will
 *  distribute incoming listenfds. 
**/
#include <unistd.h>
#include <stdio.h>
#include <sys/socket.h>
#include <sys/epoll.h>
#include <stdlib.h>
#include <netinet/in.h>
#include <string.h>
#include <net/if.h>
#include <fcntl.h>
#include <errno.h>
#include <sys/wait.h>

#define BUFFSIZE 1024
#define WORKER_NUM 50

void setnonblocking(int sockfd)
{
	int flags;

	flags = fcntl(sockfd, F_GETFL);

	if(flags < 0) {
		perror("fcntl(sockfd, GETFL)");
		exit(1);
	}

	flags = flags | O_NONBLOCK;

	if(fcntl(sockfd, F_SETFL, flags) < 0) {
		perror("fcntl(sockfd, SETFL, opts)");
		exit(1);
	}
}

int initSocket(){
    struct sockaddr_in6 address;
    int server_socket, sock, addrlen = sizeof(address), reuse = 1, port = 64002;
        // Use curl 169.254.68.39:8080
    uint32_t interfaceIndex = if_nametoindex("swissknife0");
    address.sin6_scope_id = interfaceIndex;

    if ((server_socket = socket(AF_INET6, SOCK_STREAM, 0)) == 0)
    {
        perror("socket failed");
        exit(EXIT_FAILURE);
    }
    if (setsockopt(server_socket, SOL_SOCKET, SO_REUSEADDR,
                   &reuse, sizeof(reuse)))
    {
        perror("set reuseaddr  failed");
        exit(EXIT_FAILURE);
    }

    if (setsockopt(server_socket, SOL_SOCKET, SO_REUSEPORT, &reuse, sizeof(reuse)) == -1)
    {
        perror("set reuseport failed!");
        exit(EXIT_FAILURE);
    }

    setnonblocking(server_socket);

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
    return server_socket;
}

int main(int argc, char const *argv[])
{
    char *buffer = (char *)malloc(BUFFSIZE), *ok = "HTTP/1.1 200 OK\r\nContent-Length: 22\r\nContent-Type: text/html\r\n\r\nHello World from ATeam";

    int pid = 0;
    for (int i = 0; i < WORKER_NUM ; ++i) {
        pid = fork();
        
        if (pid < 0) {
            perror("call fork failed!");
            exit(EXIT_FAILURE);
        }

        if (pid == 0)
            break;
    }

    if (pid > 0) {
        int status;
        wait(&status);
        return 0;
    }

    int server_socket = initSocket();

    int ret;
    int epfd;
    struct epoll_event ev;
    struct epoll_event evs[1024];

    epfd = epoll_create(1);
    ev.events = EPOLLIN | EPOLLET;
    ev.data.fd = server_socket;
    epoll_ctl(epfd, EPOLL_CTL_ADD, server_socket, &ev);

    int size = sizeof(evs) / sizeof(struct epoll_event);

    while (1) {
        int nfds = epoll_wait(epfd, evs, size, -1);
        for (int i = 0; i < nfds; ++i)
        {
            int curfd = evs[i].data.fd;

            if ((curfd == server_socket))
            {
                while(1){//try to accept all incoming connections
                    int conn_fd = accept(server_socket, (struct sockaddr *)NULL, NULL);

                    if(conn_fd<0){
                        if (errno != EWOULDBLOCK)
                        {
                            perror("accept failed");
                            exit(EXIT_FAILURE);
                        }
                        break;
                    }
                    setnonblocking(conn_fd);

                    ev.events = EPOLLIN | EPOLLET;
                    ev.data.fd = conn_fd;
                    if (epoll_ctl(epfd, EPOLL_CTL_ADD, conn_fd, &ev) == -1)
                    {
                        perror("Add conn_fd failed!");
                        exit(0);
                    }
                }
            }
            else
            {   //@todo:simple version, which did not check EPOLLIN/EPOLLOUT
                /*Receive all incoming data on this socket before we loop back and call select again.*/
                while(1){
	            memset(buffer, 0, sizeof(char) * BUFFSIZE);
                    int n = read(curfd, buffer, sizeof(char) * BUFFSIZE);
                    if (n == 0)
                    {
                        epoll_ctl(epfd, EPOLL_CTL_DEL, curfd, NULL);
                        close(curfd);
                        break;
                    }
                    if (n < 0)
                    {
                        if ((errno == EAGAIN) ||
                            (errno == EWOULDBLOCK))
                            break;
                        else{
                            epoll_ctl(epfd, EPOLL_CTL_DEL, curfd, NULL);
                            close(curfd);
                            break;
                        };
                    }
                    send(curfd, ok, strlen(ok), 0);
                }
            }
        }
    }
    close(epfd);
    free(buffer);
    return 0;
}
