using Godot;
using System;

public partial class Cerebrin : CharacterBody3D
{
	public const float Speed = 5.0f;
	public const float axisSpeed = 1.25f;
    public const float JumpVelocity = 4.5f;

	public override void _PhysicsProcess(double delta)
	{
		Vector3 velocity = Velocity;
		Vector3 rotation = Rotation;

		// Add the gravity.
		if (!IsOnFloor())
		{
			velocity += GetGravity() * (float)delta;
		}
		if (!IsOnFloor() && Position.Y < -10)
		{
			// Handle falling below a certain threshold (e.g., respawn or reset position)
			Position = new Vector3(0, 5, 0); // Reset position to a safe location
        }

		// Handle Jump.
		if (Input.IsActionJustPressed("ui_accept") && IsOnFloor())
		{
			velocity.Y = JumpVelocity;
		}

		// Get the input direction and handle the movement/deceleration.
		// As good practice, you should replace UI actions with custom gameplay actions.
		Vector2 inputDir = Input.GetVector("left", "right", "up", "down");
		Vector2 inputAxis = Input.GetVector("left_axis", "right_axis", "up_axis", "down_axis");
        Vector3 direction = (Transform.Basis * new Vector3(inputDir.X, 0, inputDir.Y)).Normalized();
		Vector3 orientation = (Transform.Basis * new Vector3(inputAxis.Y, inputAxis.X, 0)).Normalized();
        if (direction != Vector3.Zero || orientation != Vector3.Zero)
		{
			velocity.X = direction.X * Speed;
			velocity.Z = direction.Z * Speed;
			LookAt(orientation, Vector3.Forward);

        }
		else
		{
			velocity.X = Mathf.MoveToward(Velocity.X, 0, Speed);
			velocity.Z = Mathf.MoveToward(Velocity.Z, 0, Speed);
		}

		Velocity = velocity;
		Rotation = rotation;
        MoveAndSlide();
	}
}
