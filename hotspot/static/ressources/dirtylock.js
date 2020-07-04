
function dirtylock(delay)
{
	var lock = {};
	lock.locked = false;
	lock.dirty = false;
	lock.delay = delay;

	return lock;
}

function dirtylock_aquire(lock)
{
	if(lock.locked)
	{
		setTimeout(function(){
			lock.locked = false;
		}, lock.delay);

		return false;
	}

	lock.locked = true;

	return true;
}