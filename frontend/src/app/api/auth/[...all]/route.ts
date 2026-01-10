import { auth, ensureAuthMigrations } from "@/lib/auth";
import { toNextJsHandler } from "better-auth/next-js";

const { POST: basePost, GET: baseGet } = toNextJsHandler(auth);

export const POST = async (request: Request) => {
  await ensureAuthMigrations();
  return basePost(request);
};

export const GET = async (request: Request) => {
  await ensureAuthMigrations();
  return baseGet(request);
};
