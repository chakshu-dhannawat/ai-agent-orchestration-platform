import client from "./client";
import type { Channel, ChannelCreate } from "@/types/channel";

export async function getChannels(): Promise<Channel[]> {
  const response = await client.get<Channel[]>("/channels");
  return response.data;
}

export async function createChannel(data: ChannelCreate): Promise<Channel> {
  const response = await client.post<Channel>("/channels", data);
  return response.data;
}

export async function deleteChannel(id: string): Promise<void> {
  await client.delete(`/channels/${id}`);
}
