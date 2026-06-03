import { AlertList } from "@/components/alert-list";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { authOptions } from "@/lib/auth";
import { getAlerts } from "@/lib/api";
import { getServerSession } from "next-auth";

export default async function AlertsPage() {
    const session = await getServerSession(authOptions);
    const alerts = await getAlerts(session?.accessToken);

    return (
        <Card>
            <CardHeader>
                <div className="text-lg font-semibold">Alerts</div>
            </CardHeader>
            <CardContent>
                <AlertList alerts={alerts} token={session?.accessToken} />
            </CardContent>
        </Card>
    );
}