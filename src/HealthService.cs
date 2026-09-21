namespace DevRoomTest;

public static class HealthService
{
    public static int ClampHealth(int health)
    {
        if (health < 0) return 0;
        if (health > 100) return 100;
        return health;
    }
}
