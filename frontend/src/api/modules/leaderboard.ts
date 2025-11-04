import request from "@/utils/request";

export interface LeaderboardParams {
  period?: "day" | "week" | "month";
  metric?: "duration" | "efficiency";
  page?: number;
  page_size?: number;
}

export const leaderboardAPI = {
  getRankings(params: LeaderboardParams) {
    return request({
      url: "/api/leaderboard/",
      method: "get",
      params,
    });
  },
  getStatus() {
    return request({
      url: "/api/leaderboard/status",
      method: "get",
    });
  },
  join() {
    return request({
      url: "/api/leaderboard/join",
      method: "post",
    });
  },
  leave() {
    return request({
      url: "/api/leaderboard/leave",
      method: "post",
    });
  },
  getUserStats(userId: number, params: LeaderboardParams) {
    return request({
      url: `/api/leaderboard/users/${userId}`,
      method: "get",
      params,
    });
  },
};
