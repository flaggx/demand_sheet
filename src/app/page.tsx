import { createClient } from "@/lib/supabase/server";
import { redirect } from "next/navigation";

/**
 * `/` sends anonymous users to login; signed-in users go straight to demand data.
 */
export default async function Home() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    redirect("/login");
  }
  redirect("/dashboard/demand");
}
