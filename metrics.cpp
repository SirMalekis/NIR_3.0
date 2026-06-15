#include "metrics.h"
#include <queue>
#include <vector>
#include <numeric>
#include <algorithm>
#include <limits>

// ---------------------------------------------------------------------------
// BFS-расстояния от источника src среди активных узлов
// ---------------------------------------------------------------------------
static std::vector<int> bfsDistances(const Graph& G, int src,
                                      const std::vector<int>& active_mask) {
    int N = G.num_nodes;
    std::vector<int> dist(N, -1);
    if (!active_mask[src]) return dist;
    dist[src] = 0;
    std::queue<int> q;
    q.push(src);
    while (!q.empty()) {
        int u = q.front(); q.pop();
        for (int v : G.adj[u]) {
            if (active_mask[v] && dist[v] < 0) {
                dist[v] = dist[u] + 1;
                q.push(v);
            }
        }
    }
    return dist;
}

// ---------------------------------------------------------------------------
// Наибольшая связная компонента (BFS по активным узлам)
// ---------------------------------------------------------------------------
double computeLccRatio(const Graph& G, int N_total) {
    int N = G.num_nodes;
    std::vector<bool> visited(N, false);
    int lcc_size = 0;

    for (int s = 0; s < N; ++s) {
        if (G.nodes[s].state != 1 || visited[s]) continue;
        // BFS
        int comp_size = 0;
        std::queue<int> q;
        q.push(s);
        visited[s] = true;
        while (!q.empty()) {
            int u = q.front(); q.pop();
            ++comp_size;
            for (int v : G.adj[u]) {
                if (G.nodes[v].state == 1 && !visited[v]) {
                    visited[v] = true;
                    q.push(v);
                }
            }
        }
        lcc_size = std::max(lcc_size, comp_size);
    }
    return N_total > 0 ? (double)lcc_size / N_total : 0.0;
}

// ---------------------------------------------------------------------------
// Global Efficiency = (1/n/(n-1)) * Σ_{i≠j} 1/d(i,j)
// Вычисляем BFS от каждого активного узла — точная копия networkx.global_efficiency
// ---------------------------------------------------------------------------
double computeGlobalEfficiency(const Graph& G) {
    int N = G.num_nodes;

    // Строим маску и список активных узлов
    std::vector<int> active_mask(N, 0);
    std::vector<int> active;
    for (int i = 0; i < N; ++i) {
        if (G.nodes[i].state == 1) {
            active_mask[i] = 1;
            active.push_back(i);
        }
    }
    int na = (int)active.size();
    if (na < 2) return 0.0;

    double sum_inv = 0.0;
    for (int src : active) {
        auto dist = bfsDistances(G, src, active_mask);
        for (int v : active) {
            if (v != src && dist[v] > 0)
                sum_inv += 1.0 / dist[v];
        }
    }
    return sum_inv / ((double)na * (na - 1));
}

double computeNormalizedEfficiency(const Graph& G, double E0) {
    if (E0 <= 0.0) return 0.0;
    return computeGlobalEfficiency(G) / E0;
}

double computeWeightedSurvivability(const Graph& G) {
    double total_w = 0.0, active_w = 0.0;
    for (const auto& n : G.nodes) {
        total_w  += n.weight;
        if (n.state == 1) active_w += n.weight;
    }
    return total_w > 0.0 ? active_w / total_w : 0.0;
}

double computeInitialEfficiency(const Graph& G) {
    return computeGlobalEfficiency(G);
}
