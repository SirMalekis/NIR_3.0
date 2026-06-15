#pragma once
#include <vector>
#include <string>
#include <unordered_map>
#include <random>

// ---------------------------------------------------------------------------
// Профили типов узлов
// ---------------------------------------------------------------------------
struct NodeProfile {
    double P_attack;
    double P_recovery;
    double mu;
    int    C_repair;
    double weight;
};

extern const std::unordered_map<std::string, NodeProfile> NODE_PROFILES;
extern const std::unordered_map<std::string, double>      DEFAULT_NODE_MIX;

// ---------------------------------------------------------------------------
// Узел графа
// ---------------------------------------------------------------------------
struct Node {
    int         id;
    int         state;              // 0=отказ, 1=работает
    std::string node_type;
    double      P_attack;
    double      P_recovery;
    double      mu;
    int         C_repair;
    double      weight;
    double      recovery_end_time;  // -1=не в ремонте, inf=запрещён
};

// ---------------------------------------------------------------------------
// Граф
// ---------------------------------------------------------------------------
struct Graph {
    std::string              topology;
    int                      num_nodes;
    std::vector<Node>        nodes;
    std::vector<std::vector<int>> adj;  // списки смежности

    int degree(int n) const { return (int)adj[n].size(); }
    void addEdge(int u, int v) {
        adj[u].push_back(v);
        adj[v].push_back(u);
    }
};

// ---------------------------------------------------------------------------
// Функция создания топологии
// ---------------------------------------------------------------------------
Graph createNetworkTopology(
    const std::string& topology_type,
    int                num_nodes,
    double             base_P_attack    = 0.60,
    double             base_P_recovery  = 0.80,
    double             base_mu          = 0.20,
    int                base_C_repair    = 1,
    double             base_weight      = 1.0,
    bool               heterogeneous    = false,
    const std::unordered_map<std::string, double>& node_mix = {},
    uint64_t           seed             = 0
);
