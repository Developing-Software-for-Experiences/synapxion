using Godot;
using System;

public partial class Cerebrin : CharacterBody3D
{
    [Export] public float BaseHeight = 0.25f;
    [Export] public float FloatAmplitude = 0.25f;
    [Export] public float FloatSpeed = 1.5f;
    [Export] public float RotationSpeed = 5.0f;

    private Camera3D camera;
    private float time = 0f;

    public override void _Ready()
    {
        camera = GetViewport().GetCamera3D();
    }

    public override void _PhysicsProcess(double delta)
    {
        time += (float)delta;

        // Movimiento sinusoidal en Y
        float floatOffset = Mathf.Sin(time * FloatSpeed) * FloatAmplitude;

        Vector3 pos = Position;
        pos.Y = BaseHeight + floatOffset;
        Position = pos;

        // === ROTACIÓN HACIA EL MOUSE ===
        Vector2 mousePos = GetViewport().GetMousePosition();

        Vector3 rayOrigin = camera.ProjectRayOrigin(mousePos);
        Vector3 rayDirection = camera.ProjectRayNormal(mousePos);

        Plane plane = new Plane(Vector3.Up, 0);
        Vector3? hit = plane.IntersectsRay(rayOrigin, rayDirection);

        if (hit != null)
        {
            Vector3 target = hit.Value;
            Vector3 lookTarget = new Vector3(target.X, Position.Y, target.Z);

            Transform3D current = Transform;
            Transform3D targetTransform = current.LookingAt(lookTarget, Vector3.Up);

            Transform = current.InterpolateWith(targetTransform, (float)delta * RotationSpeed);
        }
    }
}