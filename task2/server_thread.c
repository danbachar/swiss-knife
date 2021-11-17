#include <unistd.h>
#include <stdio.h>
#include <sys/socket.h>
#include <stdlib.h>
#include <netinet/in.h>
#include <string.h>
#include <net/if.h>
#include <pthread.h>

#define BUFFSIZE 1024
#define MAX_THREAD_NUM 50
unsigned int t_cnt;
pthread_mutex_t t_lock;

const char *ok = "HTTP/1.1 200 OK\r\nContent-Length: 22\r\nContent-Type: text/html\r\n\r\nHello World from ATeam";
void* worker_foo(void* args) {
    int sock = *((int *)args);
    char *buffer = (char *)malloc(BUFFSIZE);
    memset(buffer, 0, sizeof(char) * BUFFSIZE);
    while (1)
    { //serve the client until the client close the connection
        int ret = read(sock, buffer, sizeof(char) * BUFFSIZE);
        if (ret <= 0)
        {
            close(sock);
            break;
        }
        else
        {
            printf("received: \n%s\n", buffer);
            send(sock, ok, strlen(ok), 0);
            printf("sent: \n%s\n", ok);
        }
    }

    free(buffer);
    pthread_mutex_lock(&t_lock);
    t_cnt--;
    pthread_mutex_unlock(&t_lock);
}

int main(int argc, char const *argv[])
{
    struct sockaddr_in6 address;
    int server_socket, sock, addrlen = sizeof(address), reuse = 1, port = 8080;
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
        perror("setsockopt failed");
        exit(EXIT_FAILURE);
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

    while (1)
    {
        
        if ((sock = accept(server_socket, (struct sockaddr *)&address,
                           (socklen_t *)&addrlen)) < 0)
        {
            perror("accept");
            exit(EXIT_FAILURE);
        }

        if (t_cnt < MAX_THREAD_NUM) {
            int conn_fd = sock;//give it a new address
            pthread_t tid;
            int ret = pthread_create(&tid, NULL, worker_foo, &conn_fd);
            if (ret != 0) {
                perror("Error : create thread failed.");
            } else {
                pthread_mutex_lock(&t_lock);
                t_cnt++;
                pthread_mutex_unlock(&t_lock);
                printf("create new thread, count: %d\n", t_cnt);
            }
        } else {
            printf("too_many_clients\n");
            close(sock);
        }
    }
    
    return EXIT_SUCCESS;
}
