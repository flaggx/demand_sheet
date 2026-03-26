import { redirect } from "next/navigation";

/** Hub route: send everyone to the main demand screen. */
export default function DashboardPage() {
  redirect("/dashboard/demand");
}
