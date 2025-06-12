from database import async_session, User
import asyncio

async def insert_user(username, roles, departments, access_tags):
    async with async_session() as session:
        user = User(
            username=username,
            roles=roles,
            departments=departments,
            access_tags=access_tags
        )
        session.add(user)
        await session.commit()
        print(f"Inserted user: {username} (id: {user.id})")
        return str(user.id)

# Example usage:
if __name__ == "__main__":
    # Change these values as needed for your test users
    asyncio.run(insert_user(
        username="0003",
        roles=["it_user"],
        departments=["it"],
        access_tags=["it_user","it_only"]
    ))